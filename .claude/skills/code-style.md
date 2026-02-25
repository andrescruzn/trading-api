# Code Style & Type Hints (Python 3.10+)

## 📋 PEP 8 Standards

### Nomenclatura

```python
# Clases: PascalCase
class UserService:
    pass

class OrderRepository:
    pass

# Funciones, métodos, variables: snake_case
def create_user(email: str, name: str) -> User:
    user_data = {"email": email, "name": name}
    return User(**user_data)

# Constantes: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30
API_VERSION = "v1"

# Variables privadas: _prefijo
class UserService:
    def __init__(self):
        self._cache = {}  # Privado por convención
```

---

## 🔤 Type Hints (Obligatorio - Python 3.10+)

### Sintaxis Moderna

**❌ ANTIGUO (typing module):**

```python
from typing import Optional, List, Dict, Union

def process_user(
    user_id: Optional[int],
    tags: List[str],
    metadata: Dict[str, Any]
) -> Union[User, None]:
    pass
```

**✅ MODERNO (built-in types):**

```python
def process_user(
    user_id: int | None,
    tags: list[str],
    metadata: dict[str, Any]
) -> User | None:
    pass
```

### Tipos Comunes

```python
# Básicos
def get_name() -> str: ...
def get_age() -> int: ...
def get_price() -> float: ...
def is_active() -> bool: ...

# None
def find_user(user_id: int) -> User | None: ...

# Listas
def get_tags() -> list[str]: ...
def get_users() -> list[User]: ...

# Diccionarios
def get_metadata() -> dict[str, Any]: ...
def get_counts() -> dict[str, int]: ...

# Múltiples tipos
def process(value: str | int) -> bool: ...

# Callables
from collections.abc import Callable

def execute(
    callback: Callable[[int, str], bool]
) -> None: ...
```

### Tipos Avanzados

```python
from typing import TypeVar, Generic, Protocol
from collections.abc import Sequence, Iterable

# Generic Types
T = TypeVar('T')

class Repository(Generic[T]):
    def save(self, entity: T) -> T: ...
    def find_all(self) -> list[T]: ...

# Protocol (Duck Typing)
class Serializable(Protocol):
    def to_dict(self) -> dict[str, Any]: ...

# Sequence (read-only)
def process_items(items: Sequence[str]) -> int:
    return len(items)

# Iterable
def sum_values(values: Iterable[int]) -> int:
    return sum(values)
```

---

## 🚀 FastAPI con Annotated

### Sintaxis Moderna

**❌ ANTIGUO:**

```python
from fastapi import Query, Depends

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: UserService = Depends(get_user_service)
):
    pass
```

**✅ MODERNO (Python 3.10+):**

```python
from typing import Annotated
from fastapi import Query, Depends

@router.get("/users")
async def list_users(
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    service: Annotated[UserService, Depends(get_user_service)]
):
    pass
```

### Ejemplos de Annotated

```python
from typing import Annotated
from fastapi import Query, Path, Body, Depends, Header

# Query parameters
SearchQuery = Annotated[str, Query(min_length=3, max_length=50)]
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]

@router.get("/search")
async def search(
    q: SearchQuery,
    page: PageNumber = 1,
    limit: PageSize = 20
):
    pass

# Path parameters
UserId = Annotated[int, Path(ge=1)]

@router.get("/users/{user_id}")
async def get_user(user_id: UserId):
    pass

# Body
@router.post("/users")
async def create_user(
    user: Annotated[CreateUserRequest, Body()]
):
    pass

# Headers
AuthToken = Annotated[str, Header(alias="Authorization")]

@router.get("/protected")
async def protected_route(token: AuthToken):
    pass

# Dependencies
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/profile")
async def get_profile(user: CurrentUser):
    pass
```

---

## 📝 Code Documentation

### Comentarios Estructurados

```python
# ======================================================================
# Sección Principal
# ======================================================================

class UserService:
    """
    Servicio de aplicación para gestión de usuarios.

    Responsabilidades:
    - Validar reglas de negocio
    - Orquestar operaciones de dominio
    - Coordinar con repositorios
    """

    def create_user(self, email: str, name: str) -> ServiceResult[User]:
        """
        Crear un nuevo usuario.

        Args:
            email: Email del usuario (debe ser único)
            name: Nombre completo del usuario

        Returns:
            ServiceResult con el usuario creado o error

        Business Rules:
            - Email debe ser único en el sistema
            - Email debe tener formato válido
            - Nombre no puede estar vacío
        """
        # ======================================================================
        # 1. Validar email único
        # ======================================================================
        if existing := self.repo.find_by_email(email):
            return ServiceResult.fail(
                message="El email ya está registrado",
                error_code=ErrorCode.USER_EMAIL_EXISTS
            )

        # ======================================================================
        # 2. Crear entidad de dominio
        # ======================================================================
        # La validación de formato ocurre en el constructor de User
        user = User(email=email, name=name)

        # ======================================================================
        # 3. Persistir usuario
        # ======================================================================
        saved_user = self.repo.save(user)

        # ======================================================================
        # 4. Retornar resultado exitoso
        # ======================================================================
        return ServiceResult.ok(
            data=saved_user,
            message="Usuario creado exitosamente"
        )
```

### Principios de Comentarios

✅ **Comentar:**

- **Por qué** (intención, decisión de negocio)
- Reglas de negocio complejas
- Validaciones no obvias
- Transformaciones de datos
- Queries complejas

❌ **No comentar:**

- **Qué hace** (el código debe ser auto-descriptivo)
- Código obvio
- Detalles de implementación triviales

**Ejemplo:**

```python
# ❌ MAL - Comenta lo obvio
# Incrementar contador
counter += 1

# Obtener usuario
user = self.repo.find_by_id(user_id)

# ✅ BIEN - Comenta la intención
# Incrementar intentos fallidos para aplicar rate limiting después de 3 intentos
failed_attempts += 1

# Usar cache si el usuario fue consultado recientemente (< 5 min)
# para reducir carga en BD en endpoints de alta frecuencia
user = self._get_cached_or_fetch(user_id)
```

---

## 🎨 Formatting Standards

### Separadores de Sección

```python
# ======================================================================
# Imports
# ======================================================================
from typing import Annotated
from fastapi import APIRouter, Depends

# ======================================================================
# Constants
# ======================================================================
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20

# ======================================================================
# Router Configuration
# ======================================================================
router = APIRouter(prefix="/api/v1/users", tags=["users"])

# ======================================================================
# Endpoints
# ======================================================================

@router.get("")
async def list_users(...):
    pass
```

### Orden de Imports

```python
# 1. Standard library
import os
import sys
from datetime import datetime
from typing import Annotated

# 2. Third-party
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# 3. Local
from app.common.responses import ApiResponse
from app.modules.users.domain import User
from app.modules.users.services import UserService
```

### Line Length

- **Máximo:** 100 caracteres (configurado en ruff)
- Preferir saltos de línea claros

```python
# ✅ BIEN
user = self.repo.find_by_email_and_status(
    email=email,
    status=UserStatus.ACTIVE
)

# ❌ MAL (muy largo)
user = self.repo.find_by_email_and_status(email=email, status=UserStatus.ACTIVE, include_deleted=False)
```

---

## 🛠️ Tools Configuration

### Ruff (Linter + Formatter)

Reemplaza: black, isort, flake8, pylint

**`pyproject.toml`:**

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]

ignore = [
    "E501",  # line too long (manejado por formatter)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

**Comandos:**

```bash
# Verificar errores
ruff check .

# Auto-corregir errores
ruff check --fix .

# Formatear código
ruff format .
```

---

### Mypy (Type Checker)

**`pyproject.toml`:**

```toml
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_reexport = true

# Módulos sin types
[[tool.mypy.overrides]]
module = "sqlalchemy.*"
ignore_missing_imports = true
```

**Comando:**

```bash
mypy app/
```

---

## 📦 Pydantic v2 Best Practices

### Model Configuration

```python
from pydantic import BaseModel, Field, ConfigDict

class UserResponse(BaseModel):
    """DTO de respuesta para usuario."""

    id: int = Field(description="ID único del usuario")
    email: str = Field(description="Email del usuario")
    name: str = Field(min_length=1, max_length=100)
    is_active: bool = Field(default=True, alias="isActive")

    model_config = ConfigDict(
        # Permitir acceso por nombre y alias
        populate_by_name=True,

        # Validar en asignación
        validate_assignment=True,

        # Convertir de entidad de dominio
        from_attributes=True,

        # Ejemplo en docs
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "email": "user@example.com",
                    "name": "John Doe",
                    "isActive": true
                }
            ]
        }
    )

    @classmethod
    def from_entity(cls, user: User) -> "UserResponse":
        """Convertir entidad de dominio a DTO."""
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=user.is_active
        )
```

### Validators

```python
from pydantic import field_validator, model_validator

class CreateUserRequest(BaseModel):
    email: str
    name: str
    password: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validar formato de email."""
        if '@' not in value:
            raise ValueError('Email debe contener @')
        return value.lower().strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Validar fortaleza de password."""
        if len(value) < 8:
            raise ValueError('Password debe tener al menos 8 caracteres')
        return value

    @model_validator(mode='after')
    def validate_model(self) -> 'CreateUserRequest':
        """Validaciones a nivel de modelo."""
        if self.email.startswith(self.name.lower()):
            raise ValueError('Email no puede comenzar con el nombre')
        return self
```

---

## ✅ Checklist de Calidad

Antes de commit, verificar:

```bash
# 1. Formatting
ruff format .

# 2. Linting
ruff check --fix .

# 3. Type checking
mypy app/

# 4. Tests
pytest

# 5. Coverage (opcional)
pytest --cov=app --cov-report=term-missing
```

---

**Última actualización:** Febrero 2026  
**Tokens aproximados:** ~800
