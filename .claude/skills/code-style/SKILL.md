---
name: code-style
description: Python code style for this project. Use before writing any Python code. Covers PEP 8, type hints (Python 3.10+ syntax), FastAPI with Annotated, Pydantic v2 best practices, documentation standards, and ruff/mypy configuration.
---

# Code Style & Type Hints (Python 3.10+)

## 📋 PEP 8 Standards

### Nomenclatura

```python
# Clases: PascalCase
class UserService: pass
class OrderRepository: pass

# Funciones, métodos, variables: snake_case
def create_user(email: str, name: str) -> User:
    user_data = {"email": email, "name": name}
    return User(**user_data)

# Constantes: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30

# Variables privadas: _prefijo
class UserService:
    def __init__(self):
        self._cache = {}
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
def get_name() -> str: ...
def get_age() -> int: ...
def find_user(user_id: int) -> User | None: ...
def get_tags() -> list[str]: ...
def get_metadata() -> dict[str, Any]: ...
def process(value: str | int) -> bool: ...
```

### Tipos Avanzados

```python
from typing import TypeVar, Generic, Protocol
from collections.abc import Sequence, Iterable

T = TypeVar('T')

class Repository(Generic[T]):
    def save(self, entity: T) -> T: ...
    def find_all(self) -> list[T]: ...

class Serializable(Protocol):
    def to_dict(self) -> dict[str, Any]: ...
```

---

## 🚀 FastAPI con Annotated

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

### Aliases Reutilizables

```python
SearchQuery = Annotated[str, Query(min_length=3, max_length=50)]
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]
UserId = Annotated[int, Path(ge=1)]
CurrentUser = Annotated[User, Depends(get_current_user)]
```

---

## 📝 Code Documentation

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
        """
        ...
```

### Principios de Comentarios

✅ **Comentar:** Por qué (intención, decisión de negocio), reglas complejas, validaciones no obvias
❌ **No comentar:** Qué hace el código (debe ser auto-descriptivo), código obvio

---

## 🎨 Formatting Standards

### Orden de Imports

```python
# 1. Standard library
import os
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

---

## 🛠️ Tools Configuration

### Ruff (`pyproject.toml`)

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

```bash
ruff check --fix .
ruff format .
```

---

## 📦 Pydantic v2 Best Practices

```python
from pydantic import BaseModel, Field, ConfigDict

class UserResponse(BaseModel):
    id: int = Field(description="ID único del usuario")
    email: str = Field(description="Email del usuario")
    is_active: bool = Field(default=True, alias="isActive")

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        from_attributes=True,
    )

    @classmethod
    def from_entity(cls, user: User) -> "UserResponse":
        return cls(id=user.id, email=user.email, is_active=user.is_active)
```

---

**Última actualización:** Febrero 2026
**Tokens aproximados:** ~800
