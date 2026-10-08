---
name: security
description: Seguridad de Trading App. Usar antes de tocar autenticación, roles, sesiones, inputs de usuario, credenciales de exchange, webhooks o cualquier código sensible. Cubre JWT en cookie HTTP-only con rotación de JTI, roles (user/admin/investor), rate limiting, lockout, CSP, XSS/CSRF/SQLi, bcrypt, OTP, cifrado Fernet de API keys y política de contraseñas.
---

# Security Best Practices — Trading App

## Estado actual del proyecto (ya implementado)

| Protección | Estado | Dónde |
|---|---|---|
| Rate limiting (sliding window) | ✅ | `common/security/rate_limiter.py` |
| Account lockout (3 intentos → 1h) | ✅ | `user_entity.py` + services |
| bcrypt passwords (cost 12) | ✅ | `common/security/password_hasher.py` |
| JWT HS256 + HTTP-only cookies | ✅ | `common/security/jwt/` |
| JTI rotation (revocación fuerte) | ✅ | `users/services/auth/` |
| OTP HMAC-SHA256, single-use | ✅ | `common/security/otp/` |
| Anti-enumeration en auth | ✅ | Todos los services de auth |
| Input sanitization (Bleach) | ✅ | `common/security/sanitization/` |
| CORS configurado | ✅ | `app_factory.py` |
| SameSite=Lax (CSRF básico) | ✅ | `settings.py` |
| Security headers middleware | ✅ | `common/security/security_headers.py` |
| Credenciales de exchange cifradas (Fernet) | ✅ | `common/security/credentials_cipher.py` |
| Rate limit fuera de auth | ❌ | pendiente (ver `specs/_ROOT.md`, prioridad 3) |
| Validación de URL de webhook (SSRF) | ❌ | pendiente (M9) |

---

## Roles y autorización

| Rol | ID (en BD) | Setting |
|---|---|---|
| user | 1 | `settings.AUTH_USER_ROLE_ID` |
| admin | 2 | `settings.AUTH_ADMIN_ROLE_ID` |
| investor | 3 | `settings.AUTH_INVESTOR_ROLE_ID` |

- Los *defaults* de `settings.py` coinciden con la BD (1 user, 2 admin, 3 investor). Si alguien cambia los IDs en la tabla `roles`, debe cambiarlos también en `.env`.
- Nunca hardcodear IDs; usar siempre los settings.
- Rutas solo admin: `Depends(admin_required)`. Recursos de usuario: verificar ownership (`user_id` del token) en el servicio.

## Credenciales de exchange

- API key/secret se cifran juntas con `CredentialsCipher(settings.CREDENTIALS_SECRET_KEY)` y se guardan en `accounts.credentials_ref`.
- Nunca devolverlas en respuestas ni escribirlas en logs o `audit_logs`.
- En producción `CREDENTIALS_SECRET_KEY` es obligatoria (la clave de desarrollo es fija y pública).

---

## Security Headers (OBLIGATORIO en todos los endpoints)

```python
from app.common.security.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
```

### CSP

La API es headless: todas las respuestas llevan `default-src 'none'; frame-ancestors 'none';`. La única excepción es la documentación interactiva (`/docs`, `/redoc`), que permite `cdn.jsdelivr.net` y su script inline de arranque (`_CSP_DOCS`). La CSP del frontend la pone el servidor que sirva `frontend/dist` (Nginx, Vercel…), no FastAPI.

### CORS y cookie de sesión con el frontend

- La sesión es la cookie HttpOnly `AUTH_COOKIE_NAME`; el front llama con `credentials: 'include'` y nunca ve el token.
- **Desarrollo**: el front usa el proxy `/api` de Vite → mismo origen, `SameSite=Lax` basta y CORS no interviene.
- **Producción (recomendado)**: front y API en el mismo sitio (reverse proxy `/api` o subdominios del mismo dominio) con `SameSite=Lax`. Si el front vive en otro dominio: `AUTH_COOKIE_SAMESITE=None` + HTTPS y el origen exacto en `CORS_ORIGINS` (nunca `*` con credenciales).
- **CSRF**: no hay token anti-CSRF; la protección es `SameSite` + CORS con orígenes explícitos + rutas de escritura solo por `POST/PUT/PATCH/DELETE` con JSON. Con `SameSite=None` esa defensa se debilita: antes de usarlo, añadir verificación de `Origin`.

---

## XSS Prevention

### 1. React escapa por defecto

```tsx
// ✅ Seguro: React escapa el texto
<p>{user.full_name}</p>

// ❌ PELIGROSO — prohibido con datos del usuario o de la API
<p dangerouslySetInnerHTML={{ __html: description }} />
```

En las plantillas de correo (Jinja2, `app/modules/mailer/templates/`) el autoescape sigue activo: nunca `| safe` con datos del usuario.

### 2. Bleach para HTML de usuarios

```python
from app.common.security.sanitization.html_sanitizer import sanitize_html

clean_content = sanitize_html(user_html_input)  # allowlist + strip
```

**Regla:** Texto plano → `clean_str()` de `input_cleaner.py`, NO Bleach.

### 3. HTTP-only cookies

El token JWT NUNCA se almacena en `localStorage` ni `sessionStorage`. Siempre en cookie HttpOnly → inmune a XSS.

---

## Brute Force Protection

### Capas de defensa (en orden de activación)

```
1. Rate limiter (IP + path)     → 10 req/min → HTTP 429
2. Account lockout (por email)  → 3 intentos → 1h bloqueado en DB
3. JWT JTI rotation             → sesión única activa por usuario
```

### Configuración actual

```python
auth_rate_limiter = RateLimiter(requests_per_minute=10, window_seconds=60)
AuthServiceFactory(max_failed_attempts=3, lock_minutes=60)
```

---

## SQL Injection Prevention

```python
# ✅ Correcto (parámetros named)
db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email})

# ✅ Correcto (SQLAlchemy ORM)
db.query(UserModel).filter(UserModel.email == email).first()

# ❌ PELIGROSO — NUNCA hacer esto
db.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

---

## Password Policy

```python
import re

def validate_password_strength(password: str) -> bool:
    """
    Política mínima:
    - 8+ caracteres
    - Al menos 1 mayúscula
    - Al menos 1 minúscula
    - Al menos 1 número
    """
    if len(password) < 8: return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"[a-z]", password): return False
    if not re.search(r"\d", password): return False
    return True
```

### Al cambiar contraseña

1. Verificar password actual con bcrypt
2. Validar nueva password con política
3. Nueva password ≠ password actual
4. Hashear con bcrypt (cost factor 12)
5. **Revocar sesión actual** (`token_current_jti = None`) → fuerza re-login

---

## JWT Security

### Claims mínimos requeridos

```python
{
    "sub": {"user_id": int},    # subject
    "jti": str(uuid4()),        # JWT ID único (anti-replay)
    "type": "access",
    "exp": datetime + timedelta
}
```

### Validación en cada request (jwt_guard.py)

1. Extraer token (cookie → bearer header)
2. Verificar firma HS256 + expiración
3. Verificar `type == "access"`
4. DB: `user.token_current_jti == jti` (sesión única activa)
5. DB: `user.status == "active"`
6. DB: `roles.is_active == 1`

---

## Reglas para Claude

1. NUNCA retornar tokens JWT en el body cuando se usan cookies.
2. NUNCA usar `dangerouslySetInnerHTML` en el front ni `| safe` en plantillas de correo con input de usuarios.
3. NUNCA concatenar strings en queries SQL — usar parámetros named.
4. NUNCA usar `'unsafe-inline'` en CSP.
5. SIEMPRE agregar rate limit en endpoints de auth con `Depends(check_auth_rate_limit)`.
6. SIEMPRE revocar `token_current_jti` al cambiar password o logout.
7. SIEMPRE hashear passwords y OTPs antes de persistir.
8. SIEMPRE usar `clean_email()` / `clean_str()` antes de procesar inputs.
9. Nuevas tablas con datos sensibles → nunca loguear valores, solo IDs.
10. Endpoints que aceptan HTML rico → pasar por `sanitize_html()`.
