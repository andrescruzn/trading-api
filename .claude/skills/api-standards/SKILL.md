---
name: api-standards
description: REST API standards for this project. Use before creating endpoints, responses, or error codes. Covers ApiResponse envelope format, ServiceResult pattern, error code catalog, HTTP status codes, URL conventions, and pagination structure.
---

# REST API Standards & Response Structures

## 🎯 Response Structure (Obligatorio)

Todas las respuestas de la API deben seguir este formato estándar:

### Respuesta Exitosa Simple

```json
{
  "msg": "Usuario creado exitosamente",
  "errorCode": 0,
  "data": {
    "id": 123,
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Respuesta Exitosa con Paginación

```json
{
  "msg": "Usuarios obtenidos exitosamente",
  "errorCode": 0,
  "data": {
    "items": [
      { "id": 1, "name": "User 1" },
      { "id": 2, "name": "User 2" }
    ],
    "paginate": {
      "page": 1,
      "limit": 20,
      "total": 100,
      "totalPages": 5
    }
  }
}
```

### Respuesta de Error

```json
{
  "msg": "El email ya está registrado",
  "errorCode": 1001,
  "data": null
}
```

---

## 🔢 Error Code Catalog

```python
# app/common/error_codes.py
class ErrorCode:
    SUCCESS = 0
    # Errores generales (1000-1099)
    GENERAL_ERROR = 1000
    VALIDATION_ERROR = 1001
    NOT_FOUND = 1002
    UNAUTHORIZED = 1003
    FORBIDDEN = 1004
    # Errores de usuario (1100-1199)
    USER_EMAIL_EXISTS = 1100
    USER_NOT_FOUND = 1101
    USER_INACTIVE = 1102
    USER_INVALID_CREDENTIALS = 1103
    # Errores de autenticación (1200-1299)
    TOKEN_EXPIRED = 1200
    TOKEN_INVALID = 1201
    REFRESH_TOKEN_INVALID = 1202
    # Errores de negocio específicos (1300+)
    INSUFFICIENT_BALANCE = 1300
    ORDER_ALREADY_PROCESSED = 1301
    PRODUCT_OUT_OF_STOCK = 1302
```

---

## 🔄 Flujo Service → Endpoint

### En el Service

```python
from app.common.error_codes import ErrorCode

class UserService:
    def create_user(self, email: str, name: str) -> ServiceResult[User]:
        if existing := self.repo.find_by_email(email):
            return ServiceResult.fail(
                message="El email ya está registrado",
                error_code=ErrorCode.USER_EMAIL_EXISTS
            )
        saved_user = self.repo.save(User(email=email, name=name))
        return ServiceResult.ok(data=saved_user, message="Usuario creado exitosamente")
```

### En el Endpoint REST

```python
@router.post("", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(
    request: CreateUserRequest,
    service: Annotated[UserService, Depends(get_user_service)]
) -> ApiResponse[UserResponse]:
    result = await service.create_user(email=request.email, name=request.name)
    if not result.success:
        return ApiResponse(msg=result.message, error_code=result.error_code, data=None)
    return ApiResponse(
        msg=result.message,
        error_code=ErrorCode.SUCCESS,
        data=UserResponse.from_entity(result.data)
    )
```

---

## 🌐 REST URL Conventions

```
# Colecciones
GET    /users              # Listar usuarios
POST   /users              # Crear usuario

# Recursos individuales
GET    /users/{id}         # Obtener usuario específico
PUT    /users/{id}         # Actualizar usuario completo
PATCH  /users/{id}         # Actualizar usuario parcial
DELETE /users/{id}         # Eliminar usuario

# Sub-recursos (máximo 2 niveles)
GET    /users/{id}/orders  # Órdenes de un usuario

# Acciones no-CRUD (excepciones justificadas)
POST   /users/{id}/activate
POST   /auth/login
POST   /auth/logout
```

- Sustantivos en plural: `/users`, `/products`
- kebab-case para URLs multi-palabra: `/user-profiles`
- ❌ NUNCA verbos: `/getUsers`, `/createProduct`

---

## 📊 HTTP Status Codes

```python
# Éxito
200 OK                 # GET, PUT, PATCH exitosos
201 Created            # POST exitoso (creación)
204 No Content         # DELETE exitoso

# Error del cliente
400 Bad Request        # Validación fallida
401 Unauthorized       # No autenticado
403 Forbidden          # Autenticado pero sin permisos
404 Not Found          # Recurso no existe
409 Conflict           # Conflicto (ej: email duplicado)
422 Unprocessable Entity # Validación de negocio fallida

# Error del servidor
500 Internal Server Error  # Error inesperado
```

---

## ⚠️ Reglas Críticas

❌ **NUNCA** retornar `ServiceResult` directamente desde endpoints
❌ **NUNCA** lanzar `HTTPException` desde services o dominio
❌ **NUNCA** retornar modelos ORM (SQLAlchemy) desde endpoints
❌ **NUNCA** usar `errorCode` diferente de 0 para éxito

---

**Última actualización:** Febrero 2026
**Tokens aproximados:** ~1,000
