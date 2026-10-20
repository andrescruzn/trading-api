# Módulo 1 — Auth & Frontend ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 7/7 entregables (+ 2 de 2026-10-19: endurecimiento de seguridad y vínculo de Telegram) |
| Madurez (estimada) | 84 % — ver [Avance](#avance) |
| Tablas | `users` (R/W), `roles` (R) |
| Depende de | — (es la base) |
| Lo usan | Todos los módulos (guardas `jwt_guard` / `role_guard`, helpers `owner_scope` / `is_admin`); el shell del frontend (`app-shell`) aloja todas las páginas; [M9](M09-ALERTS.md) usa el chat de Telegram vinculado |
| Prefijo API | `/api/users` (incluye `/api/users/me/telegram`) |
| Frontend | `frontend/src/modules/auth`, `app-shell`, `dashboard` |
| Última revisión | 2026-10-20 |

## Descripción

**En palabras simples:** Es la puerta de entrada al sistema. Se encarga de saber quién eres y si tienes permiso de entrar.

**Qué hace:**
- Te deja iniciar sesión **solo con un código de un solo uso (OTP)** que llega a tu correo: no hay contraseñas
- Guarda una "sesión" segura en tu navegador para que no tengas que pedir un código cada vez
- Limita cuántos códigos puedes pedir y probar por correo (sin bloquear tu cuenta); tras 5 intentos fallidos el código vigente deja de servir
- Te deja **conectar tu chat de Telegram** para aprobar desde el celular las señales de tus agentes ([M9](M09-ALERTS.md))
- Tiene dos tipos de usuario: **Administrador** (puede hacer todo) y **Usuario** (solo puede ver)

- Además es dueño del **frontend** (`frontend/`): el armazón de la app (menú lateral, migas de pan, menú de usuario), el inicio de sesión y el panel principal. Cada módulo de negocio pone sus páginas dentro de ese armazón.

**Por qué importa:** sin sesión válida no se puede usar ningún otro módulo, y el rol (`role_code` en la UI, `role_id` en la API) decide qué páginas y endpoints ve cada persona.

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Públicas:**
- `/#/login` — Inicio de sesión con código por correo: se escribe el correo, llega un OTP de 6 dígitos (cuenta regresiva y botón para reenviar). `/` redirige a `/dashboard` o `/login` según haya sesión.

**Usuario (y demás roles):**
- `/#/dashboard` — Panel principal centrado en los **agentes** ([M7](M07-BOTS-SIGNALS.md)): sin agentes, bienvenida con "Crear agente"; con agentes, KPIs, tarjeta **Señales por aprobar** (solo si hay alguna), tarjetas de los agentes (cada una con el precio, la variación y el régimen de su mercado)
- Menú de usuario (`nav-user`) → **Conectar Telegram** / **Telegram conectado**: diálogo para generar el enlace de vinculación (un solo uso, 10 min), confirmar con "Ya lo vinculé" o desvincular

**Admin / Inversor:** no tiene páginas propias; el shell solo muestra la sección "Administración" a `admin` y "Mi inversión" a `investor`.

## Entregables

Entregables:
- Login por OTP (email) — único método desde el 2026-10-08
- Dashboard con info del usuario y rol
- ~~Cambiar contraseña~~ (eliminado el 2026-10-08: no hay contraseñas)
- Logout con cookie HTTP-only
- `GET /api/users/me` (perfil del usuario autenticado)
- Security headers middleware (CSP, X-Frame-Options, etc.)
- 42 tests unitarios pasando
- ✅ (2026-10-08) Frontend React: shell con sidebar, login por código, dashboard y aviso de sesión expirada
- ✅ (2026-10-19) **Endurecimiento de seguridad**: `APP_ENV` por defecto `production`, `DEV_RETURN_OTP`, `OTP_HMAC_SECRET`, intentos fallidos del OTP persistentes, `TRUST_PROXY_HEADERS`, `OriginGuardMiddleware` (CSRF), `/docs` solo en desarrollo, `/health` sin detalles, `X-Request-ID` validado, redacción recursiva en la auditoría + script de purga, `CredentialsCipher` con rotación de claves, helpers `owner_scope` / `is_admin`
- ✅ (2026-10-19) **Vínculo de Telegram**: `POST /api/users/me/telegram/link`, `DELETE /api/users/me/telegram`, `telegram_linked` en `GET /api/users/me`, diálogo en el menú de usuario

Tablas usadas: `users`, `roles`

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| **Login solo por OTP** al correo; sin contraseñas ni cambio/reset de contraseña. Se elimina la columna `users.password_hash` | Una sola vía de acceso, sin credenciales que robar ni reutilizar; no se guarda nada que no se use | Contraseña + OTP opcional (dos superficies de ataque) · dejar la columna nullable y vacía |
| JWT HS256 en cookie **HTTP-only** (`SameSite=Lax`, `Secure` en producción) | El JS de la página no puede leer el token → mitiga robo por XSS | Token en `localStorage` / header manual |
| Rotación de `token_current_jti` en cada sesión activa | Una sola sesión válida por usuario; iniciar sesión en otro sitio invalida la anterior | Tokens sin estado revocable solo por expiración |
| `role_id` va dentro del `subject` del JWT | Lo usaban las antiguas páginas Jinja para decidir sin consultar la BD (ver gotcha); hoy `jwt_guard` lee el rol de la BD | Consultar `users` en cada página |
| Páginas admin del front redirigen a `/dashboard` (`RoleGuard` en `_app/admin.tsx` / `_app/investor.tsx`); la API responde 403 | UX: el usuario sin permiso no ve un error crudo. El guard es solo UX: el backend valida el rol en cada endpoint | 403 con página de error |
| OTP se genera con `otp_generator` y se guarda **hasheado** (`otp_hasher`) | Si se filtra la BD, los códigos no son utilizables | OTP en claro con expiración corta |
| **Anti-enumeración en el login:** `POST /users/login` responde igual (200 `otp_required`) si el correo no tiene cuenta o está inactiva, sin generar OTP ni enviar correo; en `verify`, correo sin cuenta / sin código / vencido / incorrecto → 401 con el mismo texto (`OTP_VERIFY_ERROR_MESSAGES`), y `USER_NOT_ALLOWED` solo tras un código correcto. El front dice "Si {correo} tiene una cuenta, te enviamos un código" | La pantalla no confirma qué correos están registrados | Mensaje "No encontramos una cuenta con ese correo" (eliminado el 2026-10-08) |
| **Sin lockout de cuenta; rate limit por correo e IP.** Por correo: 3 códigos pedidos y 5 intentos de verificación cada 10 min (`otp_request_rate_limiter` / `otp_verify_rate_limiter`); por IP: 10/min por ruta. Cuenta igual exista o no el correo. Pedir otro código reemplaza al anterior. Se eliminan `users.failed_attempts` y `users.login_locked_until` (migración `9ca3ab02fd7a`) | Con 6 dígitos y 10 min de vigencia, 5 intentos por ventana dejan ~1 en 200.000 de acertar; el lockout delataba qué correos tienen cuenta y dejaba bloquear cuentas ajenas | Lockout 3 fallos → 1 h (eliminado el 2026-10-08) |
| **Correo del OTP en segundo plano** (`MailerService.send_by_template_in_background` → `app/common/utils/background.py`, pool de 4 hilos, 3 intentos con esperas de 2 s y 10 s; el fallo final va al log con el correo enmascarado) | La respuesta no espera al SMTP: tarda lo mismo exista o no la cuenta y ya no hay 502 por el proveedor de correo | Envío síncrono con 502 `OTP_EMAIL_SEND_FAILED` (eliminado) · cola externa (Celery/Redis) |
| API **headless** bajo `/api` + SPA React separada (`frontend/`, hash routing) | Un solo contrato JSON para cualquier cliente; el front se despliega aparte y las URLs (`/#/bots`) no chocan con la API | Páginas Jinja2 servidas por FastAPI (eliminadas el 2026-10-08) |
| CSP única y restrictiva (`default-src 'none'`) para toda la API; excepción solo para `/docs` y `/redoc` | La API no sirve HTML propio | CSP por ruta con prefijos web |
| Sin refresh token: un 401 fuera del login cierra la sesión en el front, muestra "Tu sesión expiró" y vuelve a `/login` | Cookie HttpOnly con un solo `jti` activo; mantenerlo simple | Refresh token + rotación silenciosa |
| Roles en el front por `role_code` (`ROLES.USER/ADMIN/INVESTOR`) de `GET /api/users/me` | Independiente de los IDs de cada BD | Decidir por `role_id` o `role_label` |
| Auditoría HTTP con `AuditMiddleware` y tablas por año (`http_audit_<año>`) | Trazabilidad de todo request sin tocar el esquema principal; insert no bloqueante (inferido del código) | Solo logs de aplicación |
| **Intentos fallidos del OTP en BD** (`users.otp_failed_attempts`): al llegar a `OTP_MAX_FAILED_ATTEMPTS` (5) se borra el código vigente (`OTP_TOO_MANY_ATTEMPTS`, mismo texto que un código inválido); se pone a 0 al pedir código nuevo o al acertar | El rate limit en memoria no se comparte entre workers; la cuenta no se bloquea (solo el código) y el mensaje no delata nada | Volver al lockout de cuenta |
| `APP_ENV` por defecto **`production`** | Si se olvida en un servidor, la app exige secretos reales (fail fast) en vez de arrancar con los de desarrollo | Default `development` (antes) |
| `DEV_RETURN_OTP` (solo tiene efecto con `APP_ENV=development`) decide si el login devuelve `otp_code` | Probar sin correo en local y poder apagarlo | Depender solo de `APP_ENV` |
| `OTP_HMAC_SECRET` propio para los códigos (vacío → `JWT_SECRET_KEY`) | Filtrar un secreto no compromete el otro | Reutilizar siempre `JWT_SECRET_KEY` |
| `X-Forwarded-For` solo con `TRUST_PROXY_HEADERS=true` (`client_ip()` en `rate_limiter.py`, compartido con la auditoría) | Sin proxy propio, cualquiera falsea su IP y se salta el rate limit | Confiar siempre en la cabecera (antes) |
| **`OriginGuardMiddleware`:** POST/PUT/PATCH/DELETE con `Origin` que no está en `CORS_ORIGINS` → 403 con envelope; sin `Origin` (curl, Telegram, servidores) pasa | Defensa CSRF además de `SameSite`; con `SameSite=None` es la defensa principal | Token CSRF en cada formulario |
| `/docs`, `/redoc` y `/openapi.json` solo con `APP_ENV=development` | En producción expondrían el mapa completo de la API sin sesión | Docs siempre activos |
| `/health` sin `environment` ni el texto del error de BD (va al log) | La ruta es pública | Devolver el detalle |
| `X-Request-ID` del cliente solo si cumple `[A-Za-z0-9._-]{1,64}`; si no, se genera uno | Evita inyectar saltos de línea o textos largos en los logs | Aceptar cualquier valor |
| `X-XSS-Protection: 0` | El filtro XSS de navegadores viejos se podía abusar; la protección real es la CSP (recomendación OWASP) | `1; mode=block` (antes) |
| Auditoría: **redacción recursiva** (dicts y listas, hasta 20 niveles, sin distinguir mayúsculas) de `password`, `otp_code`, `token`, `api_key`, `api_secret`, `secret`, `passphrase`, `private_key`, `enc_creds`, `webhook`, `webhook_url`, `authorization`, `link_url`… + script `database/scripts/redact_audit_payloads.py` para las filas viejas | Hasta 2026-10 las credenciales de exchange y las URLs de webhook podían quedar en claro en `http_audit_*` | Redactar solo en la raíz y en `data` |
| `CredentialsCipher` con **MultiFernet**: cifra con `CREDENTIALS_SECRET_KEY` y descifra también con `CREDENTIALS_PREVIOUS_KEYS`; `rotate(token)` re-cifra; sin clave fuera de development/testing → `RuntimeError` (en `Settings` y en el cipher) | Rotar la clave sin perder las credenciales guardadas; nunca arrancar con la clave de ejemplo en producción | Una sola clave (cambiarla invalidaba todo) |
| `owner_scope(identity)` e `is_admin(identity)` en `app/common/security/jwt/role_guard.py` | Una sola regla de propiedad (`user_id` o `None` para admin) para todos los módulos | Copiarla en cada router |
| Vínculo de Telegram por código de un solo uso (`secrets.token_urlsafe(24)`, 10 min) guardado como **SHA-256** en `users.telegram_link_hash`; `telegram_chat_id` UNIQUE (si el chat ya era de otro usuario, se le quita) | El código no queda en claro; un chat pertenece a una sola cuenta | Guardar el código en claro o pedir el `chat_id` a mano |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (7/7) | Todos los entregables del roadmap están implementados |
| Madurez | **≈ 84 %** | Funcionalidad 100 · Tests 60 · Seguridad 95 · Operación 80 |

- **Tests (60):** hay tests de `get_me`, security headers / API headless y 3 suites de auditoría; **no hay** tests de `login_otp` ni `verify_otp` (el único camino de login, ahora con contador de intentos), `logout`, `rotate_token`, `OriginGuardMiddleware`, la redacción recursiva, `CredentialsCipher` con rotación, `TelegramLinkService`, ni tests del frontend.
- **Seguridad (95):** OTP hasheado con secreto propio, de un solo uso e invalidado tras 5 fallos; rate limit por correo e IP (IP real solo detrás de proxy de confianza); anti-enumeración; cookies seguras; defensa CSRF por `Origin`; docs ocultos en producción; auditoría sin secretos; fail fast sin claves en producción.
- **Operación (80):** rotación de la clave de credenciales sin downtime y script de purga de la auditoría; sin gestión de usuarios desde la UI; si el correo (SMTP) falla, nadie puede entrar.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Tests para `login_otp` y `verify_otp` (único camino de login, con `otp_failed_attempts`), `logout`, `rotate_token`, `OriginGuardMiddleware` y la redacción recursiva de la auditoría | S |
| Media | Extender el rate limit a `/api/candles/fetch` y `/api/orders` (desde 2026-10-19 ya cubre auth, las dos rutas de la IA y "Actualizar datos" del agente, por usuario) | S |
| Media | Script para re-cifrar todas las credenciales con la clave nueva (`CredentialsCipher.rotate`) y poder retirar `CREDENTIALS_PREVIOUS_KEYS` | S |
| Media | Tests del frontend (al menos login, api-client y guards de rol) | M |
| Media | 2FA/TOTP opcional para admin e inversores (manejan dinero) | M |
| Media | CRUD de usuarios (no hay endpoint de alta; hoy solo el seed `users`) | M |
| Media | Permitir varias sesiones (varios dispositivos) con un JTI por sesión | M |
| Media | Rate limit en Redis: hoy es en memoria (se reinicia con el proceso y no se comparte entre instancias) | S |
| Baja | Cola de correo persistente: hoy un reinicio pierde los correos aún no enviados | M |

## Fuera de alcance y pendientes conocidos

- Alta de usuarios desde la UI (no hay endpoint de registro en el módulo).
- SSO / OAuth.
- Sesiones concurrentes (hoy una sola por usuario).
- Contraseñas (login, cambio o recuperación): se eliminaron por decisión de diseño.

## Detalle técnico

### Tablas en BD
| Tabla | Uso |
|-------|-----|
| `users` | Usuarios, OTP, JTI de sesión, last_login_at (sin columnas de contraseña ni de lockout). Desde 2026-10-19: `otp_failed_attempts INT NOT NULL DEFAULT 0` (migración `218d50385270`), `telegram_chat_id BIGINT NULL` + `uq_users_telegram_chat`, `telegram_link_hash VARCHAR(64) NULL` + `idx_users_telegram_link`, `telegram_link_expires_at TIMESTAMP(6) NULL` (migración `f51e2dad9c13`) |
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
| `login_otp_service.py` | Solicitar OTP por email |
| `verify_otp_service.py` | Verificar OTP y emitir cookie |
| `logout_service.py` | Revocar cookie y limpiar JTI |
| `rotate_token_service.py` | Rotar JTI en sesión activa |
| `get_me_service.py` | Perfil del usuario autenticado (incluye `telegram_linked`) |

`app/modules/users/services/telegram/telegram_link_service.py` → `TelegramLinkService`: `create_link(user_id)` (`TELEGRAM_NOT_CONFIGURED` 503 sin `TELEGRAM_BOT_TOKEN` o `TELEGRAM_BOT_USERNAME`; devuelve `https://t.me/<bot>?start=<código>` y `expires_at`), `confirm(code, chat_id)` (lo llama el bot de Telegram, [M9](M09-ALERTS.md)), `unlink(user_id)`. Factory: `AuthServiceFactory.telegram_link()`. Repo: `get_by_telegram_chat_id`, `get_by_telegram_link_hash`.

### Endpoints (`/api/users/...`)
Todas las rutas REST se montan bajo `settings.API_PREFIX` (`/api`) en `app/app_factory.py`; el router declara `prefix="/users"`. `/health` queda en la raíz.

| Método | Ruta | Auth |
|--------|------|------|
| POST | `/api/users/login` | — (`{email}` → envía OTP por correo) |
| POST | `/api/users/login/otp/verify` | — |
| POST | `/api/users/logout` | cookie |
| POST | `/api/users/token/rotate` | cookie |
| GET  | `/api/users/me` | cookie (incluye `telegram_linked`) |
| POST | `/api/users/me/telegram/link` | cookie (enlace de vinculación de un solo uso) |
| DELETE | `/api/users/me/telegram` | cookie (desvincula el chat) |

El router de Telegram (`app/modules/users/rest/telegram/routes.py`, `prefix="/users/me/telegram"`) se registra como `telegram_link_router`; textos en `rest/telegram/error_messages.py`.

### Errores
- Todo error (401/403/404/405/422/429) sale con el envelope `{msg, errorCode, data}` (`app/common/errors/errors.py`).
- Errores del guard (`AuthException`) → texto de UI en español de `AUTH_ERROR_MESSAGES` (`app/common/errors/error_messages.py`); 422 → `data: [{field, message}]`; 429 → `data.retry_after_seconds` + header `Retry-After`.
- Mensajes de las rutas de auth: `app/modules/users/rest/auth/error_messages.py` (`OTP_VERIFY_ERROR_MESSAGES`: un solo texto para código inválido, vencido o no solicitado).

### Frontend (`frontend/src/modules/...`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/login` | `routes/_auth/login.lazy.tsx` | `auth/pages/login.tsx` + `auth/components/login-form.tsx` (correo → código, `InputOTP`, `useCountdown`) |
| `/#/dashboard` | `routes/_app/dashboard.lazy.tsx` | `dashboard/pages/dashboard.tsx` (las tarjetas son `AgentCard` de [M7](M07-BOTS-SIGNALS.md)) |

- **API:** `auth/api/auth.api.ts` (`requestOtp`, `verifyOtp`, `logout`, `me` con `telegram_linked`, y las llamadas de vincular/desvincular Telegram) y `auth/hooks/use-auth-mutations.ts`.
- **Telegram:** `app-shell/components/telegram-link-dialog.tsx` (`TelegramLinkDialog`: "Generar enlace" → "Abrir Telegram" → "Ya lo vinculé" refresca `GET /users/me`; "Desvincular"), abierto desde `nav-user.tsx` ("Conectar Telegram" / "Telegram conectado").
- **Sesión:** `auth/context/auth-provider.tsx` + `auth/hooks/use-auth.ts` (`{status, user, refreshUser, clear}`); `routes/__root.tsx` carga `GET /api/users/me` antes de renderizar. `_app.tsx` sin sesión → `/login`.
- **Roles:** `auth/lib/roles.ts` (`ROLES`), `auth/components/has-role.tsx`, `auth/hooks/use-has-role.ts`, `auth/layouts/role-guard.tsx` (`AdminGuardLayout`, `InvestorGuardLayout`).
- **Sesión expirada:** `shared/lib/api-client.ts` — un 401 fuera de `/users/login`, `/users/login/otp/verify`, `/users/logout` y `/users/me` llama `endSession(true)` → `auth/lib/session-expired-store.ts` (zustand) → `auth/components/session-expired-dialog.tsx` en `/login`. No hay refresh token.
- **Shell:** `app-shell/layouts/app-shell.tsx` (sidebar + breadcrumb), `app-shell/components/app-sidebar.tsx` (`navSections`: General, Mercado, Trading, "Mi inversión" con `role: investor`, "Administración" con `role: admin`), `nav-user.tsx` (menú de usuario: datos, Telegram y cerrar sesión), `app-brand.tsx`, `app-not-found-page.tsx`; migas con `usePageBreadcrumb`.
- **Compartido:** `shared/lib/api-client.ts` (`credentials: 'include'`, desempaqueta `{msg, errorCode, data}`, lanza `ApiClientError` si `errorCode >= 400`), `DataTable`, `OptionSelect`, `StatCard`, `PageListHeader`, `ErrorAlert`, `shared/lib/format.ts`.
- **Variables de entorno:** `.env.frontend` en la raíz (copiar de `.env.frontend.example`, no se commitea): `VITE_API_URL` (URL completa; dev `http://localhost:8000/api`, sin proxy). `pnpm dev` → `http://localhost:5193`.
- Convenciones: skill [`frontend`](../.claude/skills/frontend/SKILL.md).

### Middleware relevante
- `app/common/security/security_headers.py` — CSP restrictiva (`default-src 'none'; frame-ancestors 'none'`) en toda la API; `_is_docs_route()` relaja la CSP solo para `/docs` y `/redoc` (Swagger UI / ReDoc desde `cdn.jsdelivr.net`). `X-XSS-Protection: 0`.
- `app/common/security/origin_guard.py` — `OriginGuardMiddleware` (registrado en `app_factory.py` dentro de CORS para que el 403 lleve cabeceras CORS): escrituras con `Origin` fuera de `CORS_ORIGINS` → 403 "No se permite esta acción desde ese sitio.".
- `app/common/logging/middleware.py` — `X-Request-ID` del cliente solo si cumple `[A-Za-z0-9._-]{1,64}`.
- `app/common/security/rate_limiter.py` — `client_ip(request)` (X-Forwarded-For solo con `TRUST_PROXY_HEADERS`), `check_user_rate_limit(limiter, user_id)` y `agent_analysis_rate_limiter` ([M6](M06-AI-AGENT.md)).
- `app/common/security/jwt/role_guard.py` — `is_admin(identity)`, `owner_scope(identity)` (exportados en `app.common.security.jwt`).
- `app/common/security/credentials_cipher.py` — `CredentialsCipher.from_settings()` (MultiFernet con `CREDENTIALS_SECRET_KEY` + `CREDENTIALS_PREVIOUS_KEYS`), `rotate(token)`; lo usan [M4](M04-ACCOUNTS-PORTFOLIO.md) y [M8](M08-ORDERS-EXECUTION.md).
- `app/modules/health/rest/routes.py` — `/health` sin `environment` ni detalle del error de BD.
- `app/app_factory.py` — `docs_url`, `redoc_url` y `openapi_url` solo con `APP_ENV=development`.
- `app/common/audit/` — AuditMiddleware, tablas `http_audit_<año>`; `_resolve_event_type` quita `API_PREFIX` antes de mapear (`/api/users/login` → `/users/login`).
- `settings.CORS_ORIGINS` (dev): `http://localhost:5193`, `http://127.0.0.1:5193` y `:5173`; el front llama directo a la API con CORS (sin proxy de Vite). `localhost:5193` → `localhost:8000` es same-site, así que la cookie `SameSite=Lax` viaja; no mezclar `localhost` con `127.0.0.1`.

### Roles en BD
- `role_id=1` → Usuario (`user`)
- `role_id=2` → Administrador (`admin`)
- `role_id=3` → Inversor (`investor`, lo introduce [M10](M10-BILLING.md)) — además ve `/#/investor/dashboard`; `settings.AUTH_INVESTOR_ROLE_ID = 3`
- No hardcodear IDs: usar `settings.AUTH_ADMIN_ROLE_ID` / `settings.AUTH_USER_ROLE_ID` / `settings.AUTH_INVESTOR_ROLE_ID`.

### Auditoría HTTP (`app/common/audit/`)
- Todo request HTTP queda auditado automáticamente vía `AuditMiddleware` (`BaseHTTPMiddleware`).
- Tablas dinámicas por año: `http_audit_2026`, `http_audit_2027`… se crean solas en el primer request del año.
- **No bloqueante:** el insert se hace en un hilo daemon, no afecta la latencia del usuario.
- `event_type`: `POST /users/login` → siempre `LOGIN_OTP_REQUEST`.
- Campos redactados (`audit_sanitizer.py`, en cualquier nivel de dicts y listas, hasta 20 niveles, clave sin distinguir mayúsculas) → `"***REDACTED***"` (la clave se preserva). Request: `password`, `current_password`, `new_password`, `otp_code`, `token`, `access_token`, `api_key`, `apikey`, `api_secret`, `secret`, `passphrase`, `private_key`, `enc_creds`, `credentials_ref`, `webhook`, `webhook_url`, `authorization`. Response: `token`, `access_token`, `otp_code`, `enc_creds`, `credentials_ref`, `link_url`, `webhook`, `webhook_url`.
- Rutas excluidas: `/health`, `/docs`, `/redoc`, `/openapi.json`, `/favicon` y `/api/telegram/webhook` (lleva el código de vinculación).
- IP: `client_ip()` del rate limiter (misma regla de `TRUST_PROXY_HEADERS`).
- **Filas viejas:** `database/scripts/redact_audit_payloads.py` re-aplica el sanitizador a las tablas `http_audit_<año>` (idempotente, lotes de 500): `uv run python -m database.scripts.redact_audit_payloads --dry-run` y luego sin `--dry-run`. Después, **rotar las API keys** que pudieron quedar expuestas. Lo ejecuta el usuario.
- Para columnas `TIMESTAMP(6)` en SQLAlchemy Core usar `sqlalchemy.dialects.mysql.TIMESTAMP(fsp=6)`.

### Dashboard — agentes primero (`/#/dashboard`)
- Saludo con el nombre y cuántos agentes están analizando el mercado (`GET /api/users/me`, `GET /api/bots?mine=true`).
- **Sin agentes:** `AgentsEmptyState` (qué es un agente, cómo funciona en 3 pasos y botón "Crear agente" → `/#/agents/new`).
- **Con agentes:** 3 `StatCard` (agentes activos, paper/live, mis cuentas), aviso si ninguno está activo y hasta 6 `AgentCard` con el precio de su mercado, su última señal y controles.
- Sin sección de mercado propia (retirada el 2026-10-20): mostraba solo los dos primeros pares y, sin agentes, BTC/ETH en 1h casi siempre sin velas. El precio va en cada tarjeta y las velas en la pestaña Mercado del agente.
- Sidebar: **General** (Inicio) · **Operar** (Mis agentes, Alertas, Mis cuentas) · **Explorar** (Explorar mercados, Estrategias) · Mi inversión · Administración (Datos de mercado, Supervisión, Inversores).

## Gotchas críticos

### Gotcha crítico — JWT subject
El JWT debe incluir `role_id` para que las páginas admin funcionen:
```python
subject={"user_id": user.id, "role_id": user.role_id}
```
Servicios que crean tokens (los 2 deben tener `role_id`):
- `verify_otp_service.py`
- `rotate_token_service.py`

Histórico (UI Jinja, eliminada el 2026-10-08): sin `role_id` en el JWT, `_get_identity_from_cookie()` retornaba `role_id=0` y las páginas admin redirigían al dashboard. Hoy `jwt_guard` lee el rol de la BD y el front decide por `role_code` de `GET /api/users/me`; se mantiene `role_id` en el subject por compatibilidad.
- **NUNCA usar `curl` para hacer login durante el debugging**: cambia `token_current_jti` e invalida la sesión activa del navegador (el front verá un 401 y mostrará "Tu sesión expiró").

### Gotcha — rutas del front sin `/api`
En `frontend/src/modules/<x>/api/*.api.ts` las rutas se escriben **sin** `/api` (`api.get('/bots')`): el prefijo lo pone `VITE_API_URL`. Escribir `/api/bots` en el front genera `/api/api/bots` → 404 con envelope.

### Gotcha — `.env.frontend` vs `.env`
Vite **no** lee el `.env` del backend: `vite.config.ts` carga `.env.frontend` a mano. Solo las variables `VITE_*` llegan al navegador; nunca poner secretos ahí.

### Gotcha — `APP_ENV` vacío = producción
Desde 2026-10-19, sin `APP_ENV` la app arranca como `production`: exige `JWT_SECRET_KEY`, `CORS_ORIGINS` y `CREDENTIALS_SECRET_KEY` (si falta alguno, `RuntimeError` al arrancar), marca la cookie `Secure` y oculta `/docs`. En local hay que poner `APP_ENV=development` en el `.env`.

### Gotcha — 403 "No se permite esta acción desde ese sitio."
Lo devuelve `OriginGuardMiddleware` cuando una escritura llega con un `Origin` que no está en `CORS_ORIGINS` (p. ej. el front servido desde un host o puerto nuevo). Añadir el origen a `CORS_ORIGINS`.

### Gotcha — IP detrás de un proxy
Con `TRUST_PROXY_HEADERS=false` (por defecto) el rate limit y la auditoría usan la IP de la conexión: detrás de Nginx todos los usuarios comparten la IP del proxy. Activarlo solo con proxy propio y `uvicorn --forwarded-allow-ips=<ip del proxy>`.

### Settings nuevos (2026-10-19)
```
APP_ENV=development            # vacío → production
DEV_RETURN_OTP=true            # solo con development
TRUST_PROXY_HEADERS=false
OTP_HMAC_SECRET=               # vacío → JWT_SECRET_KEY
OTP_MAX_FAILED_ATTEMPTS=5
CREDENTIALS_PREVIOUS_KEYS=     # claves Fernet anteriores, separadas por comas (solo descifran)
TELEGRAM_BOT_USERNAME=         # para el enlace de vinculación (M9)
```

## Tests

- `tests/users/test_get_me_service.py` y 45 tests de auditoría en `tests/common/audit/` (incluye que `/users/login` se registra como `LOGIN_OTP_REQUEST` aunque llegue `password`). Los tests de `login_password` y `change_password` se eliminaron junto con esos servicios.
- `tests/common/security/test_security_headers.py`: CSP restrictiva en la API, CSP de `/docs`, `X-Frame-Options`, `nosniff`; API headless (raíz → 404 JSON, las páginas viejas ya no existen, endpoint protegido exige auth, 422 con envelope).
- `tests/web/` se eliminó junto con las páginas Jinja.
- **Huecos:** `login_otp`, `verify_otp` (único camino de login, con contador de intentos), `logout`, `rotate_token`, `OriginGuardMiddleware`, redacción recursiva y script de purga, `CredentialsCipher` con rotación, `TelegramLinkService`; sin tests del frontend. Los tests de auditoría existentes no se actualizaron para los campos nuevos (no se ejecutaron en esta revisión).

### Gotcha — anti-enumeración
- Pedir código y verificarlo responden igual exista o no la cuenta (mismo status, mismo `msg`, mismo límite por correo, correo en segundo plano).
- **Excepción en development:** `otp_code` solo viene en la respuesta si la cuenta existe y `DEV_RETURN_OTP=true` (por defecto `true`). Nunca sale con `APP_ENV` distinto de `development`.
- **Demasiados intentos:** tras `OTP_MAX_FAILED_ATTEMPTS` fallos el código se borra y la respuesta es la misma que con un código inválido (`OTP_TOO_MANY_ATTEMPTS` comparte texto); hay que pedir otro código.
- **Requiere la migración `218d50385270`** (`users.otp_failed_attempts`): sin ella `verify_otp` falla al leer o escribir el contador.
- El rate limit vive en memoria del proceso: con varias instancias de la API cada una cuenta por separado (ver mejoras).
- Si el SMTP falla tras los reintentos la persona no recibe nada y la UI no lo sabe: debe pedir otro código. Revisar el log `app.modules.mailer.services.mailer_service`.

## Riesgos

- Sesión única por usuario: un login accidental (p. ej. una prueba con `curl`) cierra la sesión del navegador.
- El correo es el único factor: si el SMTP falla nadie puede entrar, y quien controle el correo controla la cuenta.
- `JWT_SECRET_KEY` débil comprometería todas las sesiones; en desarrollo hay un valor por defecto (`dev-only-change-me`) y fuera de desarrollo `Settings` falla rápido si falta (también si falta `CREDENTIALS_SECRET_KEY`).
- Las filas de `http_audit_*` anteriores a 2026-10-19 pueden tener API keys de exchange en claro hasta que se ejecute `redact_audit_payloads.py` (y conviene rotar esas claves).
- Quien controle el chat de Telegram vinculado puede aprobar señales de la cuenta ([M9](M09-ALERTS.md)).

## Historial

- **2026-01** — Esquema inicial `users` / `roles` (roles `user`=1, `admin`=2).
- **2026-03** — Se añade `role_id` al `subject` del JWT (bug detectado en M2: las páginas admin redirigían al dashboard).
- **Posterior** — Rol `investor` (id=3) introducido por [M10](M10-BILLING.md).
- **2026-10-07** — Defaults de `AUTH_USER_ROLE_ID`/`AUTH_ADMIN_ROLE_ID` en `settings.py` corregidos (1/2, antes invertidos). `GetMeService` lee el rol con `UserRepository.get_role_info()`. Servicios de auth sin `Session`: confirman con `repo.commit()`.
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-08** — Login solo por OTP: se eliminan login con contraseña, `PATCH /users/me/password`, la página `/#/profile` y `SEED_USERS_PASSWORD`; se elimina la columna `users.password_hash` (migración `c4497f5a0188`).
- **2026-10-08** — Anti-enumeración en el login: se elimina "No encontramos una cuenta con ese correo"; el front avanza siempre al paso del código.
- **2026-10-08** — Dashboard centrado en agentes y sidebar reorganizado (Operar / Explorar); la tarjeta del login dice "Agentes con IA".
- **2026-10-08** — Se quita el lockout de cuenta (migración `9ca3ab02fd7a`) y se reemplaza por rate limit por correo; el correo del OTP sale en segundo plano (sin 502); el 429 dice cuánto esperar.
- **2026-10-19** — Auditoría de seguridad: `APP_ENV` por defecto `production`, `DEV_RETURN_OTP`, `OTP_HMAC_SECRET`, `users.otp_failed_attempts` (máx. `OTP_MAX_FAILED_ATTEMPTS`, migración `218d50385270`), `TRUST_PROXY_HEADERS`, `OriginGuardMiddleware` (CSRF), `/docs` y `/openapi.json` solo en desarrollo, `/health` sin entorno ni error de BD, `X-Request-ID` validado, `X-XSS-Protection: 0`, redacción recursiva en la auditoría + `database/scripts/redact_audit_payloads.py`, `CredentialsCipher` con MultiFernet y `CREDENTIALS_PREVIOUS_KEYS` (fail fast sin clave), `owner_scope` / `is_admin` en `role_guard.py`.
- **2026-10-19** — Vínculo de Telegram: `POST /api/users/me/telegram/link`, `DELETE /api/users/me/telegram`, `telegram_linked` en `GET /api/users/me`, columnas `users.telegram_*` (migración `f51e2dad9c13`), "Conectar Telegram" en el menú de usuario (`TelegramLinkDialog`); tarjeta "Señales por aprobar" en el dashboard.
- **2026-10-20** — Dashboard sin sección "Mercado" (y sin `price-chart.tsx`): el precio, la variación y el régimen pasan a cada tarjeta de agente (`AgentPrice` en [M7](M07-BOTS-SIGNALS.md)).
