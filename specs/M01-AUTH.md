# Módulo 1 — Auth (Autenticación) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 7/7 entregables |
| Madurez (estimada) | 88 % — ver [Avance](#avance) |
| Tablas | `users` (R/W), `roles` (R) |
| Depende de | — (es la base) |
| Lo usan | Todos los módulos (guardas `jwt_guard` / `role_guard`) |
| Prefijo API | `/users` |
| Última revisión | 2026-10-07 |

## Descripción

**En palabras simples:** Es la puerta de entrada al sistema. Se encarga de saber quién eres y si tienes permiso de entrar.

**Qué hace:**
- Te deja iniciar sesión con tu correo y contraseña
- También puedes iniciar sesión con un código de un solo uso (OTP) que llega a tu email
- Guarda una "sesión" segura en tu navegador para que no tengas que volver a escribir tu contraseña cada vez
- Si te equivocas la contraseña 3 veces, te bloquea temporalmente por seguridad
- Tiene dos tipos de usuario: **Administrador** (puede hacer todo) y **Usuario** (solo puede ver)

**Por qué importa:** sin sesión válida no se puede usar ningún otro módulo, y el rol (`role_id`) decide qué páginas y endpoints ve cada persona.

## Páginas

**Páginas:**
- `/login` — Pantalla de inicio de sesión
- `/dashboard` — Panel principal
- `/profile` — Cambiar contraseña

## Entregables

Entregables:
- Login por password y por OTP (email)
- Dashboard con info del usuario y rol
- Cambiar contraseña (revoca sesión)
- Logout con cookie HTTP-only
- GET /users/me (perfil del usuario autenticado)
- Security headers middleware (CSP, X-Frame-Options, etc.)
- 42 tests unitarios pasando

Tablas usadas: `users`, `roles`

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| JWT HS256 en cookie **HTTP-only** (`SameSite=Lax`, `Secure` en producción) | El JS de la página no puede leer el token → mitiga robo por XSS | Token en `localStorage` / header manual |
| Rotación de `token_current_jti` en cada sesión activa | Una sola sesión válida por usuario; cambiar contraseña o iniciar sesión en otro sitio invalida la anterior | Tokens sin estado revocable solo por expiración |
| `role_id` va dentro del `subject` del JWT | Las páginas admin deciden sin consultar la BD en cada request (ver gotcha) | Consultar `users` en cada página |
| Páginas admin redirigen a `/dashboard` (no devuelven 403) | UX: el usuario sin permiso no ve un error crudo en una página HTML | 403 con página de error |
| OTP se genera con `otp_generator` y se guarda **hasheado** (`otp_hasher`) | Si se filtra la BD, los códigos no son utilizables | OTP en claro con expiración corta |
| Lockout: 3 intentos fallidos → bloqueo temporal (`login_locked_until`) | Frena fuerza bruta sobre un correo concreto | Solo rate limit por IP |
| CSP por ruta en `security_headers.py` (`web_prefixes`) | Bloquea scripts/estilos inline; obliga a `addEventListener` en `/static/` | CSP global permisiva |
| Auditoría HTTP con `AuditMiddleware` y tablas por año (`http_audit_<año>`) | Trazabilidad de todo request sin tocar el esquema principal; insert no bloqueante (inferido del código) | Solo logs de aplicación |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (7/7) | Todos los entregables del roadmap están implementados |
| Madurez | **≈ 88 %** | Funcionalidad 100 · Tests 85 · Seguridad 90 · Operación 75 |

- **Tests (85):** hay tests de `login_password`, `get_me`, `change_password`, web routes y 3 suites de auditoría; **no hay** tests de `login_otp`, `verify_otp`, `logout` ni `rotate_token`.
- **Seguridad (90):** bcrypt, lockout, cookies seguras, sanitización, rate limiter en rutas de auth.
- **Operación (75):** sin gestión de usuarios desde la UI ni recuperación de contraseña.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Tests para `login_otp`, `verify_otp`, `logout` y `rotate_token` (hoy sin cobertura) | S |
| Alta | Extender `rate_limiter` más allá de las rutas de auth (hoy solo `users/rest/auth/routes.py`): `/agent/analyze` (gasta LLM), `/candles/fetch`, `/api/orders` | M |
| Media | 2FA/TOTP opcional para admin e inversores (manejan dinero) | M |
| Media | CRUD de usuarios y recuperación/restablecimiento de contraseña (no hay endpoints documentados de alta o reset) | M |
| Media | Permitir varias sesiones (varios dispositivos) con un JTI por sesión | M |
| Baja | Política de contraseñas configurable y vista de intentos fallidos/lockouts para admin | S |

## Fuera de alcance y pendientes conocidos

- Alta de usuarios desde la UI (no hay endpoint de registro en el módulo).
- SSO / OAuth.
- Sesiones concurrentes (hoy una sola por usuario).

## Detalle técnico

### Tablas en BD
| Tabla | Uso |
|-------|-----|
| `users` | Usuarios, password_hash, OTP, JTI de sesión, lockout, last_login_at |
| `roles` | id=1→user, id=2→admin |

### Modelos ORM
- `app/modules/users/infrastructure/user_model.py` → `UserModel` (tabla `users`)
- `app/modules/users/infrastructure/role_model.py` → `RoleModel` (tabla `roles`)

### Repositorios
- `app/modules/users/domain/user_repository.py` — interfaz ABC
- `app/modules/users/infrastructure/user_repository_impl.py` — `SqlAlchemyUserRepository`

### Servicios (`app/modules/users/services/auth/`)
| Archivo | Función |
|---------|---------|
| `login_password_service.py` | Login por password (bcrypt, lockout, JTI) |
| `login_otp_service.py` | Solicitar OTP por email |
| `verify_otp_service.py` | Verificar OTP y emitir cookie |
| `logout_service.py` | Revocar cookie y limpiar JTI |
| `rotate_token_service.py` | Rotar JTI en sesión activa |
| `get_me_service.py` | Perfil del usuario autenticado |
| `change_password_service.py` | Cambiar contraseña (revoca sesión) |

### Endpoints (`/users/...`)
| Método | Ruta | Auth |
|--------|------|------|
| POST | `/users/login` | — |
| POST | `/users/login-otp` | — |
| POST | `/users/verify-otp` | — |
| POST | `/users/logout` | cookie |
| POST | `/users/rotate-token` | cookie |
| GET  | `/users/me` | cookie |
| POST | `/users/change-password` | cookie |

### Páginas web
| URL | Template | JS |
|-----|----------|----|
| `/login` | `templates/login.html` | `static/js/login.js` |
| `/dashboard` | `templates/dashboard.html` | `static/js/dashboard.js` |
| `/profile` | `templates/profile.html` | `static/js/profile.js` |

### Middleware relevante
- `app/common/security/security_headers.py` — CSP por ruta
  - **IMPORTANTE:** Al agregar nuevas rutas web hay que añadirlas a `web_prefixes` en `_is_web_route()`
  - Prefijos actuales: `/login`, `/dashboard`, `/profile`, `/static/`, `/market/`, `/admin/`
- `app/common/audit/` — AuditMiddleware, tablas `http_audit_<año>`

### Roles en BD
- `role_id=1` → Usuario (`user`)
- `role_id=2` → Administrador (`admin`)
- `role_id=3` → Inversor (`investor`, lo introduce [M10](M10-BILLING.md)) — solo ve `/investor/dashboard`; `settings.AUTH_INVESTOR_ROLE_ID = 3`
- No hardcodear IDs: usar `settings.AUTH_ADMIN_ROLE_ID` / `settings.AUTH_USER_ROLE_ID` / `settings.AUTH_INVESTOR_ROLE_ID`.

### Auditoría HTTP (`app/common/audit/`)
- Todo request HTTP queda auditado automáticamente vía `AuditMiddleware` (`BaseHTTPMiddleware`).
- Tablas dinámicas por año: `http_audit_2026`, `http_audit_2027`… se crean solas en el primer request del año.
- **No bloqueante:** el insert se hace en un hilo daemon, no afecta la latencia del usuario.
- Campos redactados: `password`, `otp_code`, `token`, `access_token` → `"***REDACTED***"` (la clave se preserva).
- Rutas excluidas: `/health`, `/static/`, `/favicon`.
- Para columnas `TIMESTAMP(6)` en SQLAlchemy Core usar `sqlalchemy.dialects.mysql.TIMESTAMP(fsp=6)`.

### Dashboard — stats + gráfica (`/dashboard`, implementado en marzo de 2026)
- 4 tarjetas: BTC/USDT (dorado), ETH/USDT (cian), Mis cuentas (violeta), Estrategias (verde).
- Gráfica de línea de BTC/USDT con las últimas 48 velas de 1h, dibujada con la Canvas API (sin CDN).
- Datos reales desde: `/api/strategies`, `/accounts`, `/symbols`, `/timeframes`, `/candles`, `/candle-features`.

## Gotchas críticos

### Gotcha crítico — JWT subject
El JWT debe incluir `role_id` para que las páginas admin funcionen:
```python
subject={"user_id": user.id, "role_id": user.role_id}
```
Servicios que crean tokens (los 3 deben tener `role_id`):
- `login_password_service.py`
- `verify_otp_service.py`
- `rotate_token_service.py`

Sin `role_id` en el JWT, `_get_identity_from_cookie()` retorna `role_id=0` y todas las páginas admin redirigen silenciosamente al dashboard.
- Relacionado: las páginas admin de [M2](M02-MARKET-DATA.md) y siguientes dependen de este `role_id`.
- **NUNCA usar `curl` para hacer login durante el debugging**: cambia `token_current_jti` e invalida la sesión activa del navegador.

## Tests

- 42 tests unitarios de auth (según el roadmap) en `tests/users/` (`test_login_password_service.py`, `test_get_me_service.py`, `test_change_password_service.py`), `tests/web/test_web_routes.py` y 45 tests de auditoría en `tests/common/audit/`.
- **Huecos:** `login_otp`, `verify_otp`, `logout`, `rotate_token`.

## Riesgos

- Sesión única por usuario: un login accidental (p. ej. una prueba con `curl`) cierra la sesión del navegador.
- `JWT_SECRET_KEY` débil comprometería todas las sesiones; en desarrollo hay un valor por defecto (`dev-only-change-me`) y fuera de desarrollo `Settings` falla rápido si falta.

## Historial

- **2026-01** — Esquema inicial `users` / `roles` (roles `user`=1, `admin`=2).
- **2026-03** — Se añade `role_id` al `subject` del JWT (bug detectado en M2: las páginas admin redirigían al dashboard).
- **Posterior** — Rol `investor` (id=3) introducido por [M10](M10-BILLING.md).
