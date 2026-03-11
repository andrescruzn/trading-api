---
name: security
description: Security best practices for this project. Use before implementing authentication, authorization, input handling, or any security-sensitive code. Covers JWT cookies, rate limiting, lockout, CSP headers, XSS/CSRF/SQLi prevention, bcrypt, OTP, and password policy.
---

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

## Security Headers (OBLIGATORIO en todos los endpoints)

```python
from app.common.security.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
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

**Regla:** NUNCA usar `'unsafe-inline'` ni `'unsafe-eval'` en producción.

---

## XSS Prevention

### 1. Jinja2 auto-escaping

```html
<!-- ✅ Seguro (Jinja2 escapa automáticamente) -->
<p>{{ user.full_name }}</p>

<!-- ❌ PELIGROSO — solo para contenido confiable del sistema -->
<p>{{ description | safe }}</p>
```

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
2. NUNCA usar `| safe` en templates Jinja2 con input de usuarios.
3. NUNCA concatenar strings en queries SQL — usar parámetros named.
4. NUNCA usar `'unsafe-inline'` en CSP.
5. SIEMPRE agregar rate limit en endpoints de auth con `Depends(check_auth_rate_limit)`.
6. SIEMPRE revocar `token_current_jti` al cambiar password o logout.
7. SIEMPRE hashear passwords y OTPs antes de persistir.
8. SIEMPRE usar `clean_email()` / `clean_str()` antes de procesar inputs.
9. Nuevas tablas con datos sensibles → nunca loguear valores, solo IDs.
10. Endpoints que aceptan HTML rico → pasar por `sanitize_html()`.
