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

## 🏗️ Implementación con Pydantic v2

### Models Base

```python
# app/common/responses.py
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')

# ======================================================================
# Response Models (capa REST)
# ======================================================================

class PaginationMetadata(BaseModel):
    """Metadatos de paginación estándar."""
    page: int = Field(ge=1, description="Página actual")
    limit: int = Field(ge=1, le=100, description="Items por página")
    total: int = Field(ge=0, description="Total de items")
    total_pages: int = Field(ge=0, description="Total de páginas")


class PaginatedData(BaseModel, Generic[T]):
    """Estructura para datos paginados."""
    items: list[T]
    paginate: PaginationMetadata


class ApiResponse(BaseModel, Generic[T]):
    """
    Respuesta estándar de la API.

    - msg: Mensaje descriptivo del resultado
    - errorCode: 0 = éxito, >0 = código de error específico
    - data: Payload de la respuesta (puede ser null en errores)
    """
    msg: str
    error_code: int = Field(alias="errorCode")
    data: T | None = None

    model_config = {
        "populate_by_name": True,  # Permite usar tanto error_code como errorCode
        "json_schema_extra": {
            "examples": [
                {
                    "msg": "Operación exitosa",
                    "errorCode": 0,
                    "data": {"id": 1, "name": "Example"}
                }
            ]
        }
    }


# ======================================================================
# Service Result (capa de servicios)
# ======================================================================

class ServiceResult(Generic[T]):
    """
    Resultado de operaciones en la capa de servicios.
    Nunca debe ser retornado directamente por endpoints REST.
    """
    def __init__(
        self,
        success: bool,
        data: T | None = None,
        message: str = "",
        error_code: int = 0
    ):
        self.success = success
        self.data = data
        self.message = message
        self.error_code = error_code

    @staticmethod
    def ok(data: T, message: str = "Operación exitosa") -> "ServiceResult[T]":
        """Resultado exitoso."""
        return ServiceResult(success=True, data=data, message=message, error_code=0)

    @staticmethod
    def fail(message: str, error_code: int = 1000) -> "ServiceResult[T]":
        """Resultado fallido."""
        return ServiceResult(success=False, message=message, error_code=error_code)
```

---

## 🔢 Error Code Catalog

Mantener un catálogo centralizado de códigos de error:

```python
# app/common/error_codes.py

class ErrorCode:
    """Catálogo centralizado de códigos de error."""

    # ======================================================================
    # Éxito
    # ======================================================================
    SUCCESS = 0

    # ======================================================================
    # Errores generales (1000-1099)
    # ======================================================================
    GENERAL_ERROR = 1000
    VALIDATION_ERROR = 1001
    NOT_FOUND = 1002
    UNAUTHORIZED = 1003
    FORBIDDEN = 1004

    # ======================================================================
    # Errores de usuario (1100-1199)
    # ======================================================================
    USER_EMAIL_EXISTS = 1100
    USER_NOT_FOUND = 1101
    USER_INACTIVE = 1102
    USER_INVALID_CREDENTIALS = 1103

    # ======================================================================
    # Errores de autenticación (1200-1299)
    # ======================================================================
    TOKEN_EXPIRED = 1200
    TOKEN_INVALID = 1201
    REFRESH_TOKEN_INVALID = 1202

    # ======================================================================
    # Errores de negocio específicos (1300+)
    # ======================================================================
    INSUFFICIENT_BALANCE = 1300
    ORDER_ALREADY_PROCESSED = 1301
    PRODUCT_OUT_OF_STOCK = 1302
```

**Convenciones:**

- `0` - Éxito
- `1000-1099` - Errores generales
- `1100-1199` - Errores de usuario
- `1200-1299` - Errores de autenticación
- `1300+` - Errores de negocio específicos por módulo

---

## 🔄 Flujo Service → Endpoint

### En el Service

```python
# services/user_service.py
from app.common.error_codes import ErrorCode

class UserService:
    def create_user(self, email: str, name: str) -> ServiceResult[User]:
        # 1. Validar reglas de negocio
        if existing := self.repo.find_by_email(email):
            return ServiceResult.fail(
                message="El email ya está registrado",
                error_code=ErrorCode.USER_EMAIL_EXISTS
            )

        # 2. Crear entidad de dominio
        user = User(email=email, name=name)

        # 3. Persistir
        saved_user = self.repo.save(user)

        # 4. Retornar resultado exitoso
        return ServiceResult.ok(
            data=saved_user,
            message="Usuario creado exitosamente"
        )
```

### En el Endpoint REST

```python
# rest/endpoints/users.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from app.common.responses import ApiResponse
from app.common.error_codes import ErrorCode

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.post("", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(
    request: CreateUserRequest,
    service: Annotated[UserService, Depends(get_user_service)]
) -> ApiResponse[UserResponse]:
    """
    Crear un nuevo usuario.

    Returns:
        ApiResponse con los datos del usuario creado
    """
    # 1. Ejecutar lógica de negocio
    result = await service.create_user(
        email=request.email,
        name=request.name
    )

    # 2. Mapear resultado del servicio a respuesta HTTP
    if not result.success:
        # Opción A: Retornar error en formato estándar (preferido)
        return ApiResponse(
            msg=result.message,
            error_code=result.error_code,
            data=None
        )

    # 3. Transformar entidad a DTO de respuesta
    user_response = UserResponse.from_entity(result.data)

    # 4. Retornar respuesta exitosa
    return ApiResponse(
        msg=result.message,
        error_code=ErrorCode.SUCCESS,
        data=user_response
    )
```

### Con Paginación

```python
@router.get("", response_model=ApiResponse[PaginatedData[UserResponse]])
async def list_users(
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    service: Annotated[UserService, Depends(get_user_service)]
) -> ApiResponse[PaginatedData[UserResponse]]:
    """
    Listar usuarios con paginación.

    Returns:
        ApiResponse con lista paginada de usuarios
    """
    result = await service.list_users(page=page, limit=limit)

    if not result.success:
        return ApiResponse(
            msg=result.message,
            error_code=result.error_code,
            data=None
        )

    # Transformar entidades a DTOs
    items = [UserResponse.from_entity(user) for user in result.data.items]

    # Construir respuesta paginada
    paginated_data = PaginatedData(
        items=items,
        paginate=PaginationMetadata(
            page=result.data.page,
            limit=result.data.limit,
            total=result.data.total,
            total_pages=result.data.total_pages
        )
    )

    return ApiResponse(
        msg="Usuarios obtenidos exitosamente",
        error_code=ErrorCode.SUCCESS,
        data=paginated_data
    )
```

---

## 🌐 REST URL Conventions

### Principios RESTful

✅ **Usar sustantivos en plural:**

```
/users
/products
/orders
```

✅ **Usar kebab-case para URLs multi-palabra:**

```
/user-profiles
/order-items
/product-categories
```

❌ **Evitar verbos en las URLs:**

```
❌ /getUsers
❌ /createProduct
❌ /deleteOrder

✅ /users (GET, POST)
✅ /products (GET, POST)
✅ /orders/{id} (DELETE)
```

---

### Estructura de Endpoints

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
GET    /users/{id}/orders           # Órdenes de un usuario
POST   /users/{id}/orders           # Crear orden para un usuario
GET    /users/{id}/orders/{order_id} # Orden específica de un usuario

# Acciones no-CRUD (excepciones justificadas)
POST   /users/{id}/activate         # Acción específica
POST   /users/{id}/reset-password   # Acción específica
POST   /auth/login                  # Autenticación
POST   /auth/logout                 # Autenticación
POST   /auth/refresh-token          # Autenticación
```

---

### Query Parameters

**Filtros:**

```
GET /users?status=active&role=admin
GET /products?category=electronics&min_price=100
GET /orders?start_date=2024-01-01&end_date=2024-12-31
```

**Paginación:**

```
GET /users?page=1&limit=20
GET /products?page=2&limit=50
```

**Ordenamiento:**

```
GET /users?sort=created_at          # Ascendente
GET /users?sort=-created_at         # Descendente (con -)
GET /products?sort=price,-name      # Multi-campo
```

**Búsqueda:**

```
GET /users?search=john
GET /products?q=laptop
```

---

### Versionado de API

```
/api/v1/users
/api/v1/products
/api/v2/users  # Nueva versión
```

**Ubicar versión en la URL**, no en headers.

---

### Nombres de Operaciones FastAPI

```python
# ✅ CORRECTO - nombres descriptivos y específicos
@router.get("/users", name="list_users")
@router.post("/users", name="create_user")
@router.get("/users/{user_id}", name="get_user")
@router.put("/users/{user_id}", name="update_user")
@router.delete("/users/{user_id}", name="delete_user")

# ❌ INCORRECTO - genérico o confuso
@router.get("/users", name="users")
@router.post("/users", name="new_user")
```

---

## ⚠️ Reglas Críticas

### Services vs Endpoints

✅ **Services retornan:**

- `ServiceResult[T]` (capa de negocio)
- Nunca conocen `ApiResponse`

✅ **Endpoints retornan:**

- `ApiResponse[T]` (capa de presentación)
- Convierten `ServiceResult → ApiResponse`

### Prohibiciones

❌ **NUNCA** retornar `ServiceResult` directamente desde endpoints  
❌ **NUNCA** lanzar `HTTPException` desde services o dominio  
❌ **NUNCA** retornar modelos ORM (SQLAlchemy) desde endpoints  
❌ **NUNCA** usar `errorCode` diferente de 0 para éxito

---

## 📊 HTTP Status Codes

Usar los status codes apropiados:

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

**Ejemplo:**

```python
@router.post("", status_code=201)  # Creación exitosa
async def create_user(...):
    if not result.success:
        # Retornar con status code apropiado
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=result.message
        )
    return ApiResponse(...)
```

---

**Última actualización:** Febrero 2026  
**Tokens aproximados:** ~1,000
