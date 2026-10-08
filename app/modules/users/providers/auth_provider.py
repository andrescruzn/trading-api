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
#     result = factory.login_otp().request_login_otp(email)
#
# BENEFICIOS:
# - Configuración centralizada (longitud y vigencia del OTP)
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
    LogoutService,
    RotateTokenService,
    VerifyOtpService,
    GetMeService,
)


class AuthServiceFactory:
    """
    Factory para crear servicios de autenticación.

    Centraliza:
    - Instanciación del repositorio
    - Configuración de seguridad (longitud y vigencia del OTP)
    - Inyección de dependencias (mailer, settings)

    Ejemplo:
        factory = AuthServiceFactory(session=db)
        result = factory.login_otp().request_login_otp(email)
    """

    # ------------------------------------------------------------------
    # Configuración por defecto (seguridad)
    # ------------------------------------------------------------------
    DEFAULT_OTP_LENGTH = 6
    DEFAULT_OTP_TTL_MINUTES = 10

    def __init__(
        self,
        session: Session,
        config: Settings = settings,
        repo: UserRepository | None = None,
        otp_length: int = DEFAULT_OTP_LENGTH,
        otp_ttl_minutes: int = DEFAULT_OTP_TTL_MINUTES,
    ):
        """
        Inicializa el factory.

        Parámetros:
        - session: SQLAlchemy session (inyectada por FastAPI Depends)
        - config: Settings del sistema (default: singleton global)
        - repo: Repositorio de usuarios (opcional, para testing)
        - otp_length: longitud del OTP
        - otp_ttl_minutes: tiempo de vida del OTP
        """
        self._session = session
        self._config = config
        self._repo = repo or SqlAlchemyUserRepository(session)
        self._otp_length = otp_length
        self._otp_ttl_minutes = otp_ttl_minutes

    # ------------------------------------------------------------------
    # Factories para cada servicio
    # ------------------------------------------------------------------

    def login_otp(self) -> LoginOtpService:
        """
        Crea servicio para solicitar OTP.

        Caso de uso:
        - Usuario envía su email
        - Genera OTP
        - Envía email con código
        """
        return LoginOtpService(
            repo=self._repo,
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
            settings=self._config,
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
            settings=self._config,
        )

    def get_me(self) -> GetMeService:
        """
        Crea servicio para obtener el perfil del usuario autenticado.

        Caso de uso:
        - Usuario autenticado solicita sus propios datos
        - Alimenta el dashboard con datos reales del rol desde BD
        """
        return GetMeService(repo=self._repo)


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
            result = factory.login_otp().request_login_otp(...)
    """
    return AuthServiceFactory(session=db)
