# Estructura del Proyecto Trading API

## Visión General

```
app/
├── main.py                    # Entry point
├── app_factory.py             # Factory de la aplicación
├── common/                    # Código compartido (transversal)
├── extensions/                # Integraciones externas (DB)
└── modules/                   # Módulos de negocio
    ├── health/
    ├── mailer/
    └── users/
```

---

## Raíz de la Aplicación

| Archivo | Funcionalidad |
|---------|---------------|
| `main.py` | **Entry point**. Uvicorn busca `app.main:app`. Solo llama a `create_app()` |
| `app_factory.py` | **Factory**. Crea la app FastAPI, registra middlewares, routers y error handlers |

---

## `common/` — Código Transversal

Todo lo que se comparte entre módulos.

### `common/config/`

| Archivo | Funcionalidad |
|---------|---------------|
| `settings.py` | **Configuración central**. Lee variables de entorno (.env), valida requeridos, define defaults |
| `__init__.py` | Exporta `settings` (instancia singleton) |

**Variables de entorno soportadas:**

```env
# Entorno
APP_ENV=development|testing|production

# Base de datos
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# JWT
JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRES_MINUTES

# CORS
CORS_ORIGINS=https://app.com,https://admin.app.com

# SMTP
SMTP_HOST, SMTP_PORT, SMTP_USE_SSL, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_FROM_NAME

# Roles
AUTH_ADMIN_ROLE_ID, AUTH_USER_ROLE_ID
```

---

### `common/contracts/`

| Archivo | Funcionalidad |
|---------|---------------|
| `service_result.py` | **Contrato Service→REST**. Define `ServiceResult[T]` y `ServiceError` para respuestas estandarizadas |
| `__init__.py` | Exporta `ServiceResult`, `ServiceError` |

**Uso:**

```python
# En un service
return ServiceResult.ok(LoginPasswordPayload(...))
return ServiceResult.fail(code="INVALID_CREDENTIALS", http_status=401)

# En routes
if not result.success:
    return build_error_response(result)
return build_token_response(result.data.access_token, result.data.expires_at)
```

---

### `common/errors/`

| Archivo | Funcionalidad |
|---------|---------------|
| `error_messages.py` | **Diccionarios de mensajes**. `COMMON_ERROR_MESSAGES`, `AUTH_ERROR_MESSAGES` para traducir códigos a mensajes de UI |
| `errors.py` | **Error handlers globales**. Captura `AuthException`, `JwtCodecError` y retorna JSON estandarizado |
| `__init__.py` | Exporta handlers y mensajes |

**Mensajes disponibles:**

```python
COMMON_ERROR_MESSAGES = {
    "VALIDATION_ERROR": "Invalid request data",
    "AUTH_REQUIRED": "Authentication required",
    "FORBIDDEN": "You don't have permission to perform this action",
    "NOT_FOUND": "Resource not found",
    # ... más mensajes
}

AUTH_ERROR_MESSAGES = {
    **COMMON_ERROR_MESSAGES,
    "INVALID_CREDENTIALS": "Invalid credentials",
    "LOGIN_LOCKED": "Too many failed attempts. Please try again later.",
    "OTP_EXPIRED": "OTP has expired",
    # ... más mensajes
}
```

---

### `common/http/`

| Archivo | Funcionalidad |
|---------|---------------|
| `response_builder.py` | **Builders de respuesta**. Funciones para construir respuestas JSON estandarizadas |
| `http_responder.py` | Helper para respuestas HTTP genéricas |
| `__init__.py` | Exporta builders |

**Funciones disponibles:**

```python
build_success_response(message="OK")
build_error_response(result: ServiceResult)
build_token_response(access_token, expires_at)
build_otp_required_response(email, otp_expires_at, otp_code=None)
build_paginated_response(items, total, page, page_size)
build_data_response(data)
build_internal_error_response()
```

---

### `common/logging/`

| Archivo | Funcionalidad |
|---------|---------------|
| `logger.py` | **Logger estructurado**. JSON en producción, texto en desarrollo. Soporta `request_id` |
| `middleware.py` | **LoggingMiddleware**. Genera `request_id`, mide duración, logea cada request |
| `__init__.py` | Exporta logger y middleware |

**Uso:**

```python
from app.common.logging import get_logger

logger = get_logger(__name__)
logger.info("Usuario autenticado", extra={"user_id": 123})
```

---

### `common/security/`

| Archivo | Funcionalidad |
|---------|---------------|
| `password_hasher.py` | **Hashing de passwords**. bcrypt con cost factor 12 + migración transparente desde SHA1 legacy |
| `rate_limiter.py` | **Rate limiting**. Algoritmo sliding window, protege endpoints de fuerza bruta |
| `crypto_hash.py` | **[DEPRECADO]** SHA1 legacy, solo para compatibilidad con datos antiguos |
| `__init__.py` | Exporta todo el módulo security |

**Password Hasher:**

```python
from app.common.security import hash_password, verify_password

# Hashear nuevo password
hashed = hash_password("mi_password")  # Retorna bcrypt hash

# Verificar password
is_valid, needs_rehash = verify_password("mi_password", stored_hash)
# needs_rehash=True si el hash era SHA1 legacy
```

**Rate Limiter:**

```python
from app.common.security import check_auth_rate_limit

@router.post("/login")
def login(
    payload: LoginRequest,
    _rate_limit: None = Depends(check_auth_rate_limit),  # 10 req/min
):
    ...
```

---

### `common/security/jwt/`

| Archivo | Funcionalidad |
|---------|---------------|
| `jwt_utils.py` | **Utilidades JWT**. `create_access_token()`, `decode_access_token()`, `generate_jti()` |
| `jwt_guard.py` | **Dependency protector**. `token_required_actual()` valida JWT + DB |
| `role_guard.py` | **Guard de roles**. Verifica que el usuario tenga el rol requerido |
| `auth_exceptions.py` | **Excepciones**. `AuthException`, `JwtCodecError` |
| `__init__.py` | Exporta JWT utilities |

**JWT Guard - Validaciones:**

1. Token presente en header `Authorization: Bearer <token>`
2. Firma válida (HS256)
3. Token no expirado
4. Tipo = "access"
5. Subject contiene `user_id`
6. JTI presente
7. Usuario existe en DB
8. Usuario activo (`status = 'active'`)
9. JTI coincide con `token_current_jti` en DB
10. Rol del usuario activo

**Uso:**

```python
from app.common.security.jwt import token_required_actual

@router.post("/logout")
def logout(
    identity: dict = Depends(token_required_actual),
):
    user_id = identity["user_id"]
    role_id = identity["role_id"]
    ...
```

---

### `common/security/otp/`

| Archivo | Funcionalidad |
|---------|---------------|
| `otp_generator.py` | **Generador OTP**. `generate_numeric_otp()` crea códigos de 6 dígitos seguros |
| `otp_hasher.py` | **Hashing OTP**. HMAC-SHA256 para almacenar OTPs hasheados + soporte legacy SHA1 |
| `__init__.py` | Exporta funciones OTP |

**Uso:**

```python
from app.common.security.otp import generate_numeric_otp, hash_otp, verify_otp_hash

# Generar OTP
otp_code = generate_numeric_otp(length=6)  # Ej: "847291"

# Hashear para guardar en DB
otp_hash = hash_otp(otp_code)

# Verificar
is_valid = verify_otp_hash(otp_code, stored_hash)
```

---

### `common/security/sanitization/`

| Archivo | Funcionalidad |
|---------|---------------|
| `html_sanitizer.py` | **Sanitización HTML**. Previene XSS limpiando HTML malicioso |
| `__init__.py` | Exporta `sanitize_html()` |

---

### `common/utils/`

| Archivo | Funcionalidad |
|---------|---------------|
| `datetime_utils.py` | **Utilidades de fecha**. `utc_now()`, `ensure_aware_utc()` para manejo consistente de timezones |
| `input_cleaner.py` | **Limpieza de inputs**. `clean_email()`, `clean_str()` para sanitizar entradas |
| `__init__.py` | Exporta utilidades |

**Uso:**

```python
from app.common.utils import utc_now, ensure_aware_utc, clean_email, clean_str

now = utc_now()  # datetime con timezone UTC
aware_dt = ensure_aware_utc(naive_datetime)  # Convierte naive a UTC aware

email = clean_email("  USER@Example.COM  ")  # "user@example.com"
text = clean_str(input_text, min_len=1, max_len=255)
```

---

## `extensions/` — Integraciones Externas

### `extensions/db/`

| Archivo | Funcionalidad |
|---------|---------------|
| `config.py` | **Configuración DB**. Construye URL de conexión MySQL |
| `session.py` | **Session factory**. `get_db()` dependency para inyectar sesión SQLAlchemy |
| `base.py` | **Base declarativa**. `Base` de SQLAlchemy para modelos |
| `models_registry.py` | **Registro de modelos**. Importa todos los modelos para que SQLAlchemy los conozca (necesario para FKs) |
| `__init__.py` | Exporta `get_db`, `Base`, `engine` |

**Uso en routes:**

```python
from app.extensions.db import get_db

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    ...
```

---

## `modules/` — Módulos de Negocio

Cada módulo sigue arquitectura hexagonal:

```
module/
├── domain/           # Entidades y contratos (ports)
├── services/         # Casos de uso (application services)
├── infrastructure/   # Implementaciones (adapters)
├── providers/        # Factories para DI
└── rest/             # HTTP layer (controllers)
```

---

### `modules/health/`

**Propósito**: Health checks para Kubernetes/Docker

| Endpoint | Funcionalidad |
|----------|---------------|
| `GET /health` | Status básico `{"status": "healthy"}` |
| `GET /health/live` | Liveness probe (la app responde) |
| `GET /health/ready` | Readiness probe (DB conectada) |

---

### `modules/mailer/`

**Propósito**: Envío de emails (OTP, notificaciones)

#### `mailer/domain/`

| Archivo | Funcionalidad |
|---------|---------------|
| `mail_contracts.py` | **Interface**. `MailerPort` (ABC) define contrato para enviar emails |
| `mail_template.py` | **Templates**. Enum de plantillas de email disponibles |

#### `mailer/infrastructure/`

| Archivo | Funcionalidad |
|---------|---------------|
| `smtp_client.py` | **Adaptador SMTP**. Implementa `MailerPort` usando smtplib |
| `template_renderer.py` | **Renderizador**. Usa Jinja2 para renderizar plantillas HTML |

#### `mailer/services/`

| Archivo | Funcionalidad |
|---------|---------------|
| `mailer_service.py` | **Service**. Orquesta renderizado + envío de emails |

#### `mailer/providers/`

| Archivo | Funcionalidad |
|---------|---------------|
| `mailer_provider.py` | **Factory**. `build_mailer()` crea instancia configurada del mailer |

---

### `modules/users/`

**Propósito**: Autenticación y gestión de usuarios

#### `users/domain/`

| Archivo | Funcionalidad |
|---------|---------------|
| `user_entity.py` | **Entidad de dominio**. Clase `User` con reglas de negocio puras |
| `user_repository.py` | **Interface (Port)**. `UserRepository` ABC define contrato de persistencia |

**Reglas de negocio en `User`:**

```python
user.is_active()           # status == "active"
user.is_blocked()          # status == "blocked"
user.is_login_locked()     # login_locked_until > now
user.can_login()           # is_active() and not is_login_locked()
user.register_failed_attempt()  # Incrementa contador, lockea al 3er fallo
user.reset_failed_attempts()    # Resetea contador y lock
```

#### `users/infrastructure/`

| Archivo | Funcionalidad |
|---------|---------------|
| `user_model.py` | **Modelo ORM**. `UserModel` mapea tabla `users` |
| `role_model.py` | **Modelo ORM**. `RoleModel` mapea tabla `roles` |
| `user_repository_impl.py` | **Adaptador**. `SqlAlchemyUserRepository` implementa `UserRepository` |

#### `users/services/auth/`

| Archivo | Caso de uso |
|---------|-------------|
| `login_password_service.py` | Login con email + password → token JWT |
| `login_otp_service.py` | Solicitar OTP → genera código, envía email |
| `verify_otp_service.py` | Verificar OTP → valida código, emite token JWT |
| `logout_service.py` | Logout → revoca sesión (`token_current_jti = NULL`) |
| `rotate_token_service.py` | Renovar token → nuevo JWT, invalida anterior |

#### `users/providers/`

| Archivo | Funcionalidad |
|---------|---------------|
| `auth_provider.py` | **Factory**. `AuthServiceFactory` crea servicios con dependencias inyectadas |

**Uso:**

```python
factory = AuthServiceFactory(session=db)
result = factory.login_password().login(email, password)
result = factory.login_otp().request_login_otp(email)
result = factory.verify_otp().verify(email, otp_code)
result = factory.logout().logout(user_id)
result = factory.rotate_token().rotate(user_id)
```

#### `users/rest/auth/`

| Archivo | Funcionalidad |
|---------|---------------|
| `routes.py` | **Endpoints HTTP** |
| `schemas.py` | **Pydantic schemas** para request/response |
| `error_messages.py` | Re-exporta mensajes de error |

**Endpoints:**

| Método | Ruta | Funcionalidad |
|--------|------|---------------|
| POST | `/users/login` | Login (password u OTP) |
| POST | `/users/login/otp/verify` | Verificar OTP |
| POST | `/users/logout` | Logout (requiere token) |
| POST | `/users/token/rotate` | Renovar token (requiere token) |

---

## Diagramas de Flujo

### Login con Password

```
┌─────────────────────────────────────────────────────────────────────┐
│                         POST /users/login                           │
│                    { email, password }                              │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  routes.py                                                          │
│  1. Valida schema (Pydantic)                                        │
│  2. Rate limit check (10 req/min)                                   │
│  3. factory.login_password().login(email, password)                 │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  login_password_service.py                                          │
│  1. clean_email(), clean_str()                                      │
│  2. repo.get_by_email() → User                                      │
│  3. user.is_login_locked()? → fail("LOGIN_LOCKED")                  │
│  4. user.is_active()? → fail("USER_NOT_ALLOWED")                    │
│  5. verify_password() → bcrypt check                                │
│  6. Fallo? → user.register_failed_attempt() → fail                  │
│  7. Éxito? → create_access_token() → ok(LoginPasswordPayload)       │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  routes.py                                                          │
│  - build_token_response() o build_error_response()                  │
│  - Retorna JSONResponse                                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Login con OTP

```
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 1: Solicitar OTP                                              │
│  POST /users/login { email }  (sin password)                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  login_otp_service.py                                               │
│  1. Buscar usuario                                                  │
│  2. Generar OTP (6 dígitos)                                         │
│  3. Hashear OTP (HMAC-SHA256)                                       │
│  4. Guardar hash + expiry en DB                                     │
│  5. Enviar email con código                                         │
│  6. Retornar otp_required                                           │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 2: Verificar OTP                                              │
│  POST /users/login/otp/verify { email, otp_code }                   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  verify_otp_service.py                                              │
│  1. Buscar usuario                                                  │
│  2. Verificar OTP existe y no expiró                                │
│  3. verify_otp_hash() → comparar hashes                             │
│  4. Fallo? → register_failed_attempt()                              │
│  5. Éxito? → create_access_token() → limpiar OTP                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Patrones por Capa

| Capa | Archivos | Patrón |
|------|----------|--------|
| **REST** | `routes.py`, `schemas.py` | Controller, DTO |
| **Services** | `*_service.py` | Application Service, ServiceResult |
| **Domain** | `*_entity.py`, `*_repository.py` | Entity, Repository (Port) |
| **Infrastructure** | `*_model.py`, `*_repository_impl.py` | ORM Model, Repository (Adapter) |
| **Providers** | `*_provider.py` | Factory, Dependency Injection |

---

## Cómo Agregar un Nuevo Módulo

Ejemplo: módulo `trading`

### 1. Crear estructura

```
app/modules/trading/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── order_entity.py        # Entidad de dominio
│   └── order_repository.py    # Interface (ABC)
├── services/
│   ├── __init__.py
│   └── create_order_service.py
├── infrastructure/
│   ├── __init__.py
│   ├── order_model.py         # SQLAlchemy model
│   └── order_repository_impl.py
├── providers/
│   ├── __init__.py
│   └── trading_provider.py    # Factory
└── rest/
    ├── __init__.py
    ├── routes.py
    └── schemas.py
```

### 2. Usar contratos comunes

```python
# En services
from app.common.contracts import ServiceResult

def create_order(...) -> ServiceResult[OrderPayload]:
    ...
    return ServiceResult.ok(OrderPayload(...))
```

### 3. Usar response builders

```python
# En routes
from app.common.http import build_error_response, build_data_response

@router.post("/orders")
def create_order(...):
    result = factory.create_order().execute(...)
    if not result.success:
        return build_error_response(result)
    return build_data_response(result.data)
```

### 4. Registrar router

```python
# En app_factory.py
from app.modules.trading.rest import trading_router

app.include_router(trading_router)
```

---

## Seguridad Implementada

| Mecanismo | Implementación |
|-----------|----------------|
| **Password hashing** | bcrypt (cost 12) + migración SHA1 |
| **OTP hashing** | HMAC-SHA256 |
| **Rate limiting** | Sliding window, 10 req/min en auth |
| **Lockout** | 3 intentos → bloqueo 1 hora |
| **JWT revocación** | JTI en DB, revocación inmediata |
| **Anti-enumeration** | Mismo error para usuario inexistente y password incorrecto |
| **Input sanitization** | `clean_email()`, `clean_str()`, `sanitize_html()` |
| **Role validation** | Verifica `roles.is_active` en cada request |
| **CORS** | Lista explícita de orígenes permitidos |

---

## Comandos Útiles

```bash
# Desarrollo
uvicorn app.main:app --reload

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Ver estructura
tree -a -I "__pycache__|*.pyc|.venv|.git|.DS_Store"
```
