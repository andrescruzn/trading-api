# Security Best Practices — Trading AI API

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

---

## CAPTCHA — Decisión

### ❌ No usar CAPTCHA visible en este proyecto

**Razones:**
- Rate limiting: 10 req/min por IP bloquea ataques automatizados
- Account lockout: 3 intentos fallidos → bloqueo 1h en DB
- OTP flow: verificación humana implícita
- CAPTCHA visible agrega fricción sin beneficio real en este stack

### ✅ Si en el futuro se necesita más protección

Usar **Cloudflare Turnstile** (invisible, sin fricción):
```html
<!-- En el form de login -->
<div class="cf-turnstile" data-sitekey="YOUR_SITE_KEY"></div>
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>
```
```python
# En el service: verificar el token cf-turnstile-response
import httpx
response = httpx.post("https://challenges.cloudflare.com/turnstile/v0/siteverify", data={
    "secret": TURNSTILE_SECRET,
    "response": turnstile_token,
})
```

**Alternativas en orden de preferencia:**
1. Cloudflare Turnstile (gratis, invisible)
2. hCaptcha (privacidad-first)
3. reCAPTCHA v3 (invisible, score-based)

---

## Security Headers (OBLIGATORIO en todos los endpoints)

Usar `SecurityHeadersMiddleware` en `app_factory.py`:

```python
from app.common.security.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
```

### Headers que agrega el middleware

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Content-Security-Policy: [ver abajo]
Strict-Transport-Security: max-age=31536000; includeSubDomains  ← solo producción
```

### CSP para páginas web (Jinja2)

```
default-src 'self';
script-src 'self';
style-src 'self';
img-src 'self' data:;
font-src 'self';
connect-src 'self';
frame-ancestors 'none';
base-uri 'self';
form-action 'self';
```

### CSP para endpoints API pura (sin páginas)

```
default-src 'none';
frame-ancestors 'none';
```

**Regla:** NUNCA usar `'unsafe-inline'` ni `'unsafe-eval'` en producción.

---

## XSS Prevention

### 1. Jinja2 auto-escaping (server-side)

Jinja2 escapa por defecto en templates `.html`. **NUNCA usar `| safe` con input del usuario.**

```html
<!-- ✅ Seguro (Jinja2 escapa automáticamente) -->
<p>{{ user.full_name }}</p>

<!-- ❌ PELIGROSO — solo para contenido confiable del sistema -->
<p>{{ description | safe }}</p>
```

### 2. Bleach para HTML de usuarios

Usar `sanitize_html()` SOLO cuando el endpoint acepta contenido HTML rico:

```python
from app.common.security.sanitization.html_sanitizer import sanitize_html

clean_content = sanitize_html(user_html_input)  # allowlist + strip
```

**Regla:** Texto plano (emails, nombres, passwords) → `clean_str()` de `input_cleaner.py`, NO Bleach.

### 3. HTTP-only cookies

El token JWT NUNCA se almacena en `localStorage` ni `sessionStorage`. Siempre en cookie HttpOnly. El JS no puede leerlo → inmune a XSS.

### 4. CSP como última línea de defensa

El CSP bloquea ejecución de scripts inyectados aunque el HTML esté comprometido.

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
# auth_rate_limiter: 10 req/min en /login, /login/otp/verify
auth_rate_limiter = RateLimiter(requests_per_minute=10, window_seconds=60)

# Account lockout: 3 intentos → 60 min
AuthServiceFactory(max_failed_attempts=3, lock_minutes=60)
```

### Headers de rate limit (agregar a endpoints sensibles)

```python
# En el response de 429
headers={"Retry-After": str(retry_after_seconds)}
```

### Limitación del rate limiter actual (en memoria)

- ⚠️ No persiste entre reinicios del servidor
- ⚠️ No comparte estado entre múltiples instancias (no distribuido)
- ✅ Suficiente para servidor único o desarrollo
- **Producción multi-instancia → migrar a Redis:**

```python
# Futuro: redis-py + sliding window en Redis
import redis
r = redis.Redis(...)
pipe = r.pipeline()
pipe.zadd(key, {str(now): now})
pipe.zremrangebyscore(key, 0, now - window)
pipe.zcard(key)
pipe.expire(key, window)
results = pipe.execute()
count = results[2]
```

---

## CSRF Protection

### Estrategia actual: SameSite=Lax + CORS

Con cookies `SameSite=Lax`:
- ✅ Protege contra requests cross-site con cookies
- ✅ Permite navegación normal (GET cross-site desde links)
- ✅ Bloquea POST/PATCH/DELETE cross-site automáticos

### Si se necesita SameSite=None (cross-origin con cookies)

Agregar CSRF token:

```python
# En el middleware o endpoint: generar CSRF token
import secrets
csrf_token = secrets.token_hex(32)

# En el form (Jinja2):
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">

# En el endpoint: verificar
if request.form.get("csrf_token") != session_csrf_token:
    raise HTTPException(status_code=403, detail="CSRF token invalid")
```

---

## SQL Injection Prevention

### Regla: SIEMPRE usar parámetros, NUNCA f-strings en SQL

```python
# ✅ Correcto (parámetros named)
db.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email}
)

# ✅ Correcto (SQLAlchemy ORM)
db.query(UserModel).filter(UserModel.email == email).first()

# ❌ PELIGROSO — NUNCA hacer esto
db.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

SQLAlchemy ORM protege automáticamente contra SQL injection. Las queries raw con `text()` son seguras mientras se usen parámetros.

---

## Password Policy

### Política obligatoria para nuevas contraseñas

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
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
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

### Reglas de emisión

```python
# ✅ Claims mínimos requeridos
{
    "sub": {"user_id": int},    # subject
    "jti": str(uuid4()),        # JWT ID único (anti-replay)
    "type": "access",           # tipo de token
    "exp": datetime + timedelta # expiración
}
```

### Validación en cada request protegido (jwt_guard.py)

1. Extraer token (cookie → bearer header)
2. Verificar firma HS256 + expiración
3. Verificar `type == "access"`
4. Verificar `sub.user_id` presente
5. Verificar `jti` presente
6. DB: `user.token_current_jti == jti` (sesión única activa)
7. DB: `user.status == "active"`
8. DB: `roles.is_active == 1`

### Expiración

- Default: 1 hora (`JWT_ACCESS_TOKEN_EXPIRES_MINUTES=60`)
- Override vía env: `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`
- Al expirar → usar `POST /users/token/rotate` (rota JTI, emite nuevo)

---

## Reglas para Claude

1. NUNCA retornar tokens JWT en el body cuando se usan cookies (usar `build_cookie_auth_response`).
2. NUNCA usar `| safe` en templates Jinja2 con input de usuarios.
3. NUNCA concatenar strings en queries SQL — usar parámetros named.
4. NUNCA usar `'unsafe-inline'` en CSP.
5. SIEMPRE agregar rate limit en endpoints de auth con `Depends(check_auth_rate_limit)`.
6. SIEMPRE revocar `token_current_jti` al cambiar password o logout.
7. SIEMPRE hashear passwords y OTPs antes de persistir.
8. SIEMPRE usar `clean_email()` / `clean_str()` antes de procesar inputs.
9. Nuevas tablas con datos sensibles → nunca loguear valores, solo IDs.
10. Endpoints que aceptan HTML rico → pasar por `sanitize_html()`.
