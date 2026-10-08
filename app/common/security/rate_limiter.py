# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/rate_limiter.py
#
# PROPÓSITO:
# - Rate limiting en memoria para proteger endpoints sensibles.
# - Prevenir ataques de fuerza bruta y abuso de API.
#
# PATRÓN: Sliding Window Counter
#
# DOS FORMAS DE LLAVE:
# - Por IP + path (dependency `check_auth_rate_limit`).
# - Por correo (`check_email_rate_limit`): frena la fuerza bruta sobre el
#   login por OTP aunque el atacante rote IPs. Cuenta igual exista o no la
#   cuenta, así que no revela qué correos están registrados.
#
# LIMITACIONES:
# - En memoria: no persiste entre reinicios.
# - No distribuido: no comparte estado entre instancias.
# - Para producción distribuida, usar Redis.
#
# USO:
#     from app.common.security.rate_limiter import rate_limit_dependency
#
#     @router.post("/login")
#     def login(
#         _: None = Depends(rate_limit_dependency(requests_per_minute=10)),
#     ):
#         ...
# ======================================================================

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Callable, Dict, List, Optional

from fastapi import Request


class RateLimitExceeded(Exception):
    """Se superó el límite de peticiones; `register_error_handlers` la responde como 429."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("RATE_LIMIT_EXCEEDED")
        self.retry_after_seconds = retry_after_seconds


class RateLimiter:
    """
    Rate limiter basado en sliding window.

    Algoritmo:
    - Mantiene lista de timestamps de requests por key (IP + path).
    - Limpia requests fuera de la ventana.
    - Rechaza si excede el límite.

    Thread-safe mediante Lock.
    """

    # Con más llaves que esto en memoria, se barren las vencidas para que
    # muchos correos/IP distintos no hagan crecer el dict sin límite.
    _SWEEP_THRESHOLD = 10_000

    def __init__(
        self,
        requests_per_minute: int = 60,
        window_seconds: int = 60,
    ):
        """
        Inicializa el rate limiter.

        Parámetros:
        - requests_per_minute: máximo de requests permitidos por ventana
        - window_seconds: tamaño de la ventana en segundos
        """
        self._limit = requests_per_minute
        self._window = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def _get_key(self, request: Request) -> str:
        """
        Genera key única por IP + endpoint.

        Decisión:
        - IP + path para limitar por endpoint específico.
        - Permite diferentes límites por endpoint.
        """
        # Obtener IP real (considerando proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"{client_ip}:{request.url.path}"

    def _cleanup(self, key: str, now: float) -> None:
        """Elimina requests fuera de la ventana (y la llave si queda vacía)."""
        cutoff = now - self._window
        recent = [t for t in self._requests.get(key, ()) if t > cutoff]
        if recent:
            self._requests[key] = recent
        else:
            self._requests.pop(key, None)

    def _sweep(self, now: float) -> None:
        """Barre todas las llaves vencidas cuando el dict crece demasiado."""
        if len(self._requests) < self._SWEEP_THRESHOLD:
            return
        for key in list(self._requests):
            self._cleanup(key, now)

    def check(self, request: Request) -> None:
        """
        Verifica rate limit por IP + path.

        Lanza RateLimitExceeded (429 con envelope, ver errors.py) si excede el límite.
        """
        self.check_key(self._get_key(request))

    def check_key(self, key: str) -> None:
        """
        Verifica rate limit para una llave arbitraria (p. ej. un correo).

        Lanza RateLimitExceeded (429 con envelope, ver errors.py) si excede el límite.
        """
        now = time.time()

        with self._lock:
            self._sweep(now)
            self._cleanup(key, now)

            if len(self._requests[key]) >= self._limit:
                # Calcular tiempo de espera
                oldest = self._requests[key][0] if self._requests[key] else now
                retry_after = int(self._window - (now - oldest)) + 1

                raise RateLimitExceeded(retry_after_seconds=retry_after)

            self._requests[key].append(now)

    def get_remaining(self, request: Request) -> int:
        """
        Retorna requests restantes para la key.

        Útil para headers X-RateLimit-Remaining.
        """
        key = self._get_key(request)
        now = time.time()

        with self._lock:
            self._cleanup(key, now)
            return max(0, self._limit - len(self._requests[key]))

    def reset(self) -> None:
        """
        Limpia todos los contadores.

        Útil para testing.
        """
        with self._lock:
            self._requests.clear()


# ======================================================================
# Instancias globales para diferentes niveles de protección
# ======================================================================

# Rate limiter estricto para endpoints de autenticación
auth_rate_limiter = RateLimiter(requests_per_minute=10, window_seconds=60)

# Rate limiters por correo para el login por OTP (ventana = vigencia del OTP).
# - Pedir código: 3 por correo cada 10 min.
# - Verificar código: 5 intentos por correo cada 10 min → con 6 dígitos,
#   adivinar un código vigente es ~1 en 200.000.
otp_request_rate_limiter = RateLimiter(requests_per_minute=3, window_seconds=600)
otp_verify_rate_limiter = RateLimiter(requests_per_minute=5, window_seconds=600)

# Rate limiter moderado para endpoints generales
default_rate_limiter = RateLimiter(requests_per_minute=60, window_seconds=60)

# Rate limiter relajado para endpoints públicos
public_rate_limiter = RateLimiter(requests_per_minute=120, window_seconds=60)


# ======================================================================
# Dependency para FastAPI
# ======================================================================

def rate_limit_dependency(
    requests_per_minute: int = 60,
    limiter: Optional[RateLimiter] = None,
) -> Callable:
    """
    Crea dependency de rate limiting para FastAPI.

    Uso:
        @router.post("/login")
        def login(
            request: Request,
            _: None = Depends(rate_limit_dependency(requests_per_minute=10)),
        ):
            ...

    O con limiter predefinido:
        @router.post("/login")
        def login(
            request: Request,
            _: None = Depends(rate_limit_dependency(limiter=auth_rate_limiter)),
        ):
            ...
    """
    _limiter = limiter or RateLimiter(requests_per_minute=requests_per_minute)

    def dependency(request: Request) -> None:
        _limiter.check(request)

    return dependency


def check_auth_rate_limit(request: Request) -> None:
    """
    Dependency directa para endpoints de autenticación.

    Uso simplificado:
        @router.post("/login")
        def login(
            request: Request,
            _: None = Depends(check_auth_rate_limit),
        ):
            ...
    """
    auth_rate_limiter.check(request)


def check_email_rate_limit(limiter: RateLimiter, email: str) -> None:
    """
    Rate limit por correo (normalizado a minúsculas y sin espacios).

    Uso (en la ruta, con el email ya validado por Pydantic):
        check_email_rate_limit(otp_request_rate_limiter, payload.email)
    """
    limiter.check_key(f"email:{email.strip().lower()}")
