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

from fastapi import HTTPException, Request


class RateLimiter:
    """
    Rate limiter basado en sliding window.

    Algoritmo:
    - Mantiene lista de timestamps de requests por key (IP + path).
    - Limpia requests fuera de la ventana.
    - Rechaza si excede el límite.

    Thread-safe mediante Lock.
    """

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
        """Elimina requests fuera de la ventana."""
        cutoff = now - self._window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def check(self, request: Request) -> None:
        """
        Verifica rate limit.

        Lanza HTTPException 429 si excede el límite.
        """
        key = self._get_key(request)
        now = time.time()

        with self._lock:
            self._cleanup(key, now)

            if len(self._requests[key]) >= self._limit:
                # Calcular tiempo de espera
                oldest = self._requests[key][0] if self._requests[key] else now
                retry_after = int(self._window - (now - oldest)) + 1

                raise HTTPException(
                    status_code=429,
                    detail={
                        "msg": "Too many requests. Please try again later.",
                        "errorCode": 429,
                        "data": [],
                        "retry_after_seconds": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

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
