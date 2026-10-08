# Módulo 1 — Auth & Frontend ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 7/7 entregables |
| Madurez (estimada) | 88 % — ver [Avance](#avance) |
| Tablas | `users` (R/W), `roles` (R) |
| Depende de | — (es la base) |
| Lo usan | Todos los módulos (guardas `jwt_guard` / `role_guard`); el shell del frontend (`app-shell`) aloja todas las páginas |
| Prefijo API | `/api/users` |
| Frontend | `frontend/src/modules/auth`, `app-shell`, `profile`, `dashboard` |
| Última revisión | 2026-10-08 |

## Descripción

**En palabras simples:** Es la puerta de entrada al sistema. Se encarga de saber quién eres y si tienes permiso de entrar.

**Qué hace:**
- Te deja iniciar sesión con tu correo y contraseña
- También puedes iniciar sesión con un código de un solo uso (OTP) que llega a tu email
- Guarda una "sesión" segura en tu navegador para que no tengas que volver a escribir tu contraseña cada vez
- Si te equivocas la contraseña 3 veces, te bloquea temporalmente por seguridad
- Tiene dos tipos de usuario: **Administrador** (puede hacer todo) y **Usuario** (solo puede ver)

- Además es dueño del **frontend** (`frontend/`): el armazón de la app (menú lateral, migas de pan, menú de usuario), el inicio de sesión, el panel principal y el cambio de contraseña. Cada módulo de negocio pone sus páginas dentro de ese armazón.

**Por qué importa:** sin sesión válida no se puede usar ningún otro módulo, y el rol (`role_code` en la UI, `role_id` en la API) decide qué páginas y endpoints ve cada persona.

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Públicas:**
- `/#/login` — Inicio de sesión con dos pestañas: **Contraseña** o **Código por correo** (OTP de 6 dígitos con cuenta regresiva y botón para reenviar). `/` redirige a `/dashboard` o `/login` según haya sesión.

**Usuario (y demás roles):**
- `/#/dashboard` — Panel principal (saludo, último ingreso, 4 tarjetas y gráfica de BTC/USDT)
- `/#/profile` — Cambiar contraseña

**Admin / Inversor:** no tiene páginas propias; el shell solo muestra la sección "Administración" a `admin` y "Mi inversión" a `investor`.

## Entregables

Entregables:
- Login por password y por OTP (email)
- Dashboard con info del usuario y rol
- Cambiar contraseña (revoca sesión)
- Logout con cookie HTTP-only
- `GET /api/users/me` (perfil del usuario autenticado)
- Security headers middleware (CSP, X-Frame-Options, etc.)
- 42 tests unitarios pasando
- ✅ (2026-10-08) Frontend React: shell con sidebar, login password/OTP, perfil, dashboard y aviso de sesión expirada

Tablas usadas: `users`, `roles`

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| JWT HS256 en cookie **HTTP-only** (`SameSite=Lax`, `Secure` en producción) | El JS de la página no puede leer el token → mitiga robo por XSS | Token en `localStorage` / header manual |
| Rotación de `token_current_jti` en cada sesión activa | Una sola sesión válida por usuario; cambiar contraseña o iniciar sesión en otro sitio invalida la anterior | Tokens sin estado revocable solo por expiración |
| `role_id` va dentro del `subject` del JWT | Lo usaban las antiguas páginas Jinja para decidir sin consultar la BD (ver gotcha); hoy `jwt_guard` lee el rol de la BD | Consultar `users` en cada página |
| Páginas admin del front redirigen a `/dashboard` (`RoleGuard` en `_app/admin.tsx` / `_app/investor.tsx`); la API responde 403 | UX: el usuario sin permiso no ve un error crudo. El guard es solo UX: el backend valida el rol en cada endpoint | 403 con página de error |
| OTP se genera con `otp_generator` y se guarda **hasheado** (`otp_hasher`) | Si se filtra la BD, los códigos no son utilizables | OTP en claro con expiración corta |
| Lockout: 3 intentos fallidos → bloqueo temporal (`login_locked_until`) | Frena fuerza bruta sobre un correo concreto | Solo rate limit por IP |
| API **headless** bajo `/api` + SPA React separada (`frontend/`, hash routing) | Un solo contrato JSON para cualquier cliente; el front se despliega aparte y las URLs (`/#/bots`) no chocan con la API | Páginas Jinja2 servidas por FastAPI (eliminadas el 2026-10-08) |
| CSP única y restrictiva (`default-src 'none'`) para toda la API; excepción solo para `/docs` y `/redoc` | La API no sirve HTML propio | CSP por ruta con prefijos web |
| Sin refresh token: un 401 fuera del login cierra la sesión en el front, muestra "Tu sesión expiró" y vuelve a `/login` | Cookie HttpOnly con un solo `jti` activo; mantenerlo simple | Refresh token + rotación silenciosa |
| Roles en el front por `role_code` (`ROLES.USER/ADMIN/INVESTOR`) de `GET /api/users/me` | Independiente de los IDs de cada BD | Decidir por `role_id` o `role_label` |
| Auditoría HTTP con `AuditMiddleware` y tablas por año (`http_audit_<año>`) | Trazabilidad de todo request sin tocar el esquema principal; insert no bloqueante (inferido del código) | Solo logs de aplicación |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (7/7) | Todos los entregables del roadmap están implementados |
| Madurez | **≈ 88 %** | Funcionalidad 100 · Tests 85 · Seguridad 90 · Operación 75 |

- **Tests (85):** hay tests de `login_password`, `get_me`, `change_password`, security headers / API headless y 3 suites de auditoría; **no hay** tests de `login_otp`, `verify_otp`, `logout` ni `rotate_token`, ni tests del frontend.
- **Seguridad (90):** bcrypt, lockout, cookies seguras, sanitización, rate limiter en rutas de auth.
- **Operación (75):** sin gestión de usuarios desde la UI ni recuperación de contraseña.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Tests para `login_otp`, `verify_otp`, `logout` y `rotate_token` (hoy sin cobertura) | S |
| Alta | Extender `rate_limiter` más allá de las rutas de auth (hoy solo `users/rest/auth/routes.py`): `/api/agent/analyze` (gasta LLM), `/api/candles/fetch`, `/api/orders` | M |
| Media | Tests del frontend (al menos login, api-client y guards de rol) | M |
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

### Endpoints (`/api/users/...`)
Todas las rutas REST se montan bajo `settings.API_PREFIX` (`/api`) en `app/app_factory.py`; el router declara `prefix="/users"`. `/health` queda en la raíz.

| Método | Ruta | Auth |
|--------|------|------|
| POST | `/api/users/login` | — (con `password` → login; sin `password` → envía OTP por correo) |
| POST | `/api/users/login/otp/verify` | — |
| POST | `/api/users/logout` | cookie |
| POST | `/api/users/token/rotate` | cookie |
| GET  | `/api/users/me` | cookie |
| PATCH | `/api/users/me/password` | cookie (revoca la sesión y borra la cookie) |

### Errores
- Todo error (401/403/404/405/422/429) sale con el envelope `{msg, errorCode, data}` (`app/common/errors/errors.py`).
- Errores del guard (`AuthException`) → texto de UI en español de `AUTH_ERROR_MESSAGES` (`app/common/errors/error_messages.py`); 422 → `data: [{field, message}]`; 429 → `data.retry_after_seconds` + header `Retry-After`.
- Mensajes de las rutas de auth: `app/modules/users/rest/auth/error_messages.py` (`OTP_REQUEST_ERROR_MESSAGES`, `CHANGE_PASSWORD_ERROR_MESSAGES`).

### Frontend (`frontend/src/modules/...`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/login` | `routes/_auth/login.lazy.tsx` | `auth/pages/login.tsx` + `auth/components/login-form.tsx` (pestañas Contraseña / Código por correo, `InputOTP`, `useCountdown`) |
| `/#/dashboard` | `routes/_app/dashboard.lazy.tsx` | `dashboard/pages/dashboard.tsx` + `dashboard/components/price-chart.tsx` + `dashboard/hooks/use-symbol-snapshot.ts` |
| `/#/profile` | `routes/_app/profile.lazy.tsx` | `profile/pages/profile.tsx` (usa `useChangePasswordMutation`) |

- **API:** `auth/api/auth.api.ts` (`login`, `requestOtp`, `verifyOtp`, `logout`, `me`, `changePassword`) y `auth/hooks/use-auth-mutations.ts`.
- **Sesión:** `auth/context/auth-provider.tsx` + `auth/hooks/use-auth.ts` (`{status, user, refreshUser, clear}`); `routes/__root.tsx` carga `GET /api/users/me` antes de renderizar. `_app.tsx` sin sesión → `/login`.
- **Roles:** `auth/lib/roles.ts` (`ROLES`), `auth/components/has-role.tsx`, `auth/hooks/use-has-role.ts`, `auth/layouts/role-guard.tsx` (`AdminGuardLayout`, `InvestorGuardLayout`).
- **Sesión expirada:** `shared/lib/api-client.ts` — un 401 fuera de `/users/login`, `/users/login/otp/verify`, `/users/logout` y `/users/me` llama `endSession(true)` → `auth/lib/session-expired-store.ts` (zustand) → `auth/components/session-expired-dialog.tsx` en `/login`. No hay refresh token.
- **Shell:** `app-shell/layouts/app-shell.tsx` (sidebar + breadcrumb), `app-shell/components/app-sidebar.tsx` (`navSections`: General, Mercado, Trading, "Mi inversión" con `role: investor`, "Administración" con `role: admin`), `nav-user.tsx` (menú de usuario / cerrar sesión), `app-brand.tsx`, `app-not-found-page.tsx`; migas con `usePageBreadcrumb`.
- **Compartido:** `shared/lib/api-client.ts` (`credentials: 'include'`, desempaqueta `{msg, errorCode, data}`, lanza `ApiClientError` si `errorCode >= 400`), `DataTable`, `OptionSelect`, `StatCard`, `PageListHeader`, `ErrorAlert`, `shared/lib/format.ts`.
- **Variables de entorno:** `.env.frontend` en la raíz (copiar de `.env.frontend.example`, no se commitea): `VITE_API_URL` (dev `/api` vía proxy de Vite) y `VITE_API_PROXY_TARGET` (default `http://localhost:8000`). `pnpm dev` → `http://localhost:5193`.
- Convenciones: skill [`frontend`](../.claude/skills/frontend/SKILL.md).

### Middleware relevante
- `app/common/security/security_headers.py` — CSP restrictiva (`default-src 'none'; frame-ancestors 'none'`) en toda la API; `_is_docs_route()` relaja la CSP solo para `/docs` y `/redoc` (Swagger UI / ReDoc desde `cdn.jsdelivr.net`).
- `app/common/audit/` — AuditMiddleware, tablas `http_audit_<año>`; `_resolve_event_type` quita `API_PREFIX` antes de mapear (`/api/users/login` → `/users/login`).
- `settings.CORS_ORIGINS` (dev): `http://localhost:5193`, `http://127.0.0.1:5193` y `:5173`; en dev normalmente se usa el proxy `/api` de Vite (mismo origen, cookie `SameSite=Lax`).

### Roles en BD
- `role_id=1` → Usuario (`user`)
- `role_id=2` → Administrador (`admin`)
- `role_id=3` → Inversor (`investor`, lo introduce [M10](M10-BILLING.md)) — además ve `/#/investor/dashboard`; `settings.AUTH_INVESTOR_ROLE_ID = 3`
- No hardcodear IDs: usar `settings.AUTH_ADMIN_ROLE_ID` / `settings.AUTH_USER_ROLE_ID` / `settings.AUTH_INVESTOR_ROLE_ID`.

### Auditoría HTTP (`app/common/audit/`)
- Todo request HTTP queda auditado automáticamente vía `AuditMiddleware` (`BaseHTTPMiddleware`).
- Tablas dinámicas por año: `http_audit_2026`, `http_audit_2027`… se crean solas en el primer request del año.
- **No bloqueante:** el insert se hace en un hilo daemon, no afecta la latencia del usuario.
- Campos redactados: `password`, `otp_code`, `token`, `access_token` → `"***REDACTED***"` (la clave se preserva).
- Rutas excluidas: `/health`, `/docs`, `/redoc`, `/openapi.json`, `/favicon`.
- Para columnas `TIMESTAMP(6)` en SQLAlchemy Core usar `sqlalchemy.dialects.mysql.TIMESTAMP(fsp=6)`.

### Dashboard — stats + gráfica (`/#/dashboard`)
- Saludo con el nombre y último ingreso (`GET /api/users/me`).
- 4 `StatCard`: BTC/USDT y ETH/USDT (precio, variación y badge de régimen), Mis cuentas (paper · live) y Estrategias (tendencia · reversión).
- Gráfica de línea de BTC/USDT con el cierre de las últimas 48 velas de 1h, en SVG propio (`price-chart.tsx`, sin librería), verde/rojo con tokens del tema.
- Datos reales desde: `/api/strategies`, `/api/accounts`, `/api/symbols`, `/api/timeframes`, `/api/candles`, `/api/candle-features`.

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

Histórico (UI Jinja, eliminada el 2026-10-08): sin `role_id` en el JWT, `_get_identity_from_cookie()` retornaba `role_id=0` y las páginas admin redirigían al dashboard. Hoy `jwt_guard` lee el rol de la BD y el front decide por `role_code` de `GET /api/users/me`; se mantiene `role_id` en el subject por compatibilidad.
- **NUNCA usar `curl` para hacer login durante el debugging**: cambia `token_current_jti` e invalida la sesión activa del navegador (el front verá un 401 y mostrará "Tu sesión expiró").

### Gotcha — rutas del front sin `/api`
En `frontend/src/modules/<x>/api/*.api.ts` las rutas se escriben **sin** `/api` (`api.get('/bots')`): el prefijo lo pone `VITE_API_URL`. Escribir `/api/bots` en el front genera `/api/api/bots` → 404 con envelope.

### Gotcha — `.env.frontend` vs `.env`
Vite **no** lee el `.env` del backend: `vite.config.ts` carga `.env.frontend` a mano. Solo las variables `VITE_*` llegan al navegador; nunca poner secretos ahí.

## Tests

- 42 tests unitarios de auth (según el roadmap) en `tests/users/` (`test_login_password_service.py`, `test_get_me_service.py`, `test_change_password_service.py`) y 45 tests de auditoría en `tests/common/audit/`.
- `tests/common/security/test_security_headers.py`: CSP restrictiva en la API, CSP de `/docs`, `X-Frame-Options`, `nosniff`; API headless (raíz → 404 JSON, las páginas viejas ya no existen, endpoint protegido exige auth, 422 con envelope).
- `tests/web/` se eliminó junto con las páginas Jinja.
- **Huecos:** `login_otp`, `verify_otp`, `logout`, `rotate_token`; sin tests del frontend.

## Riesgos

- Sesión única por usuario: un login accidental (p. ej. una prueba con `curl`) cierra la sesión del navegador.
- `JWT_SECRET_KEY` débil comprometería todas las sesiones; en desarrollo hay un valor por defecto (`dev-only-change-me`) y fuera de desarrollo `Settings` falla rápido si falta.

## Historial

- **2026-01** — Esquema inicial `users` / `roles` (roles `user`=1, `admin`=2).
- **2026-03** — Se añade `role_id` al `subject` del JWT (bug detectado en M2: las páginas admin redirigían al dashboard).
- **Posterior** — Rol `investor` (id=3) introducido por [M10](M10-BILLING.md).
- **2026-10-07** — Defaults de `AUTH_USER_ROLE_ID`/`AUTH_ADMIN_ROLE_ID` en `settings.py` corregidos (1/2, antes invertidos). `GetMeService` lee el rol con `UserRepository.get_role_info()`. Servicios de auth sin `Session`: confirman con `repo.commit()`.
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
