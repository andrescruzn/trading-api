# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/providers/auth_provider.py
#
# PROPÓSITO:
# - Factory para crear servicios de autenticación con dependencias.
# - Centraliza configuración y reduce duplicación en routes.
#
# PATRÓN: Factory + Dependency Injection
#
# USO EN ROUTES:
#     factory = get_auth_factory(db)
#     result = factory.login_password().login(email, password)
#
# BENEFICIOS:
# - Configuración centralizada (max_attempts, lock_minutes, etc.)
# - Fácil de testear (se puede inyectar mock factory)
# - Reduce boilerplate en endpoints
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings, Settings
from app.modules.mailer.providers import build_mailer
from app.modules.users.domain import UserRepository
from app.modules.users.infrastructure import SqlAlchemyUserRepository
from app.modules.users.services.auth import (
    LoginOtpService,
    LoginPasswordService,
    LogoutService,
    RotateTokenService,
    VerifyOtpService,
    GetMeService,
    ChangePasswordService,
)


class AuthServiceFactory:
    """
    Factory para crear servicios de autenticación.

    Centraliza:
    - Instanciación del repositorio
    - Configuración de seguridad (max_attempts, lock_minutes)
    - Inyección de dependencias (mailer, settings)

    Ejemplo:
        factory = AuthServiceFactory(session=db)
        result = factory.login_password().login(email, password)
    """

    # ------------------------------------------------------------------
    # Configuración por defecto (seguridad)
    # ------------------------------------------------------------------
    DEFAULT_MAX_FAILED_ATTEMPTS = 3
    DEFAULT_LOCK_MINUTES = 60
    DEFAULT_OTP_LENGTH = 6
    DEFAULT_OTP_TTL_MINUTES = 10

    def __init__(
        self,
        session: Session,
        config: Settings = settings,
        repo: UserRepository | None = None,
        max_failed_attempts: int = DEFAULT_MAX_FAILED_ATTEMPTS,
        lock_minutes: int = DEFAULT_LOCK_MINUTES,
        otp_length: int = DEFAULT_OTP_LENGTH,
        otp_ttl_minutes: int = DEFAULT_OTP_TTL_MINUTES,
    ):
        """
        Inicializa el factory.

        Parámetros:
        - session: SQLAlchemy session (inyectada por FastAPI Depends)
        - config: Settings del sistema (default: singleton global)
        - repo: Repositorio de usuarios (opcional, para testing)
        - max_failed_attempts: intentos antes de lockout
        - lock_minutes: duración del lockout
        - otp_length: longitud del OTP
        - otp_ttl_minutes: tiempo de vida del OTP
        """
        self._session = session
        self._config = config
        self._repo = repo or SqlAlchemyUserRepository(session)
        self._max_failed_attempts = max_failed_attempts
        self._lock_minutes = lock_minutes
        self._otp_length = otp_length
        self._otp_ttl_minutes = otp_ttl_minutes

    # ------------------------------------------------------------------
    # Factories para cada servicio
    # ------------------------------------------------------------------

    def login_password(self) -> LoginPasswordService:
        """
        Crea servicio para login por password.

        Caso de uso:
        - Usuario envía email + password
        - Valida credenciales
        - Emite token JWT
        """
        return LoginPasswordService(
            repo=self._repo,
            session=self._session,
            settings=self._config,
            max_failed_attempts=self._max_failed_attempts,
            lock_minutes=self._lock_minutes,
        )

    def login_otp(self) -> LoginOtpService:
        """
        Crea servicio para solicitar OTP.

        Caso de uso:
        - Usuario envía solo email (sin password)
        - Genera OTP
        - Envía email con código
        """
        return LoginOtpService(
            repo=self._repo,
            session=self._session,
            settings=self._config,
            mailer=build_mailer(self._config),
            otp_length=self._otp_length,
            otp_ttl_minutes=self._otp_ttl_minutes,
        )

    def verify_otp(self) -> VerifyOtpService:
        """
        Crea servicio para verificar OTP.

        Caso de uso:
        - Usuario envía email + otp_code
        - Valida código
        - Emite token JWT
        """
        return VerifyOtpService(
            repo=self._repo,
            session=self._session,
            settings=self._config,
            max_failed_attempts=self._max_failed_attempts,
            lock_minutes=self._lock_minutes,
        )

    def logout(self) -> LogoutService:
        """
        Crea servicio para logout.

        Caso de uso:
        - Usuario con token válido
        - Revoca sesión (token_current_jti = NULL)
        """
        return LogoutService(
            repo=self._repo,
            session=self._session,
        )

    def rotate_token(self) -> RotateTokenService:
        """
        Crea servicio para rotación de token.

        Caso de uso:
        - Usuario con token válido próximo a expirar
        - Emite nuevo token
        - Invalida token anterior
        """
        return RotateTokenService(
            repo=self._repo,
            session=self._session,
            settings=self._config,
        )

    def get_me(self) -> GetMeService:
        """
        Crea servicio para obtener el perfil del usuario autenticado.

        Caso de uso:
        - Usuario autenticado solicita sus propios datos
        - Alimenta el dashboard con datos reales del rol desde BD
        """
        return GetMeService(repo=self._repo, session=self._session)

    def change_password(self) -> ChangePasswordService:
        """
        Crea servicio para cambiar la contraseña.

        Caso de uso:
        - Usuario autenticado cambia su contraseña
        - Verifica password actual + política + revoca sesión
        """
        return ChangePasswordService(
            repo=self._repo,
            session=self._session,
        )


# ======================================================================
# Dependency para FastAPI
# ======================================================================

def get_auth_factory(db: Session) -> AuthServiceFactory:
    """
    Dependency helper para usar en routes.

    Uso:
        @router.post("/login")
        def login(
            payload: LoginRequest,
            factory: AuthServiceFactory = Depends(get_auth_factory),
        ):
            result = factory.login_password().login(...)
    """
    return AuthServiceFactory(session=db)
