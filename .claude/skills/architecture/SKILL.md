---
name: architecture
description: Architecture patterns and design principles for this project. Use before deciding on patterns, SOLID principles, sub-modularization, or domain structure. Covers Repository, ServiceResult, Factory, Strategy patterns with Python examples.
---

# Architecture Patterns & Design Principles

## 🎯 Core Principles

### SOLID

- **S**ingle Responsibility - Un componente = una responsabilidad
- **O**pen/Closed - Abierto para extensión, cerrado para modificación
- **L**iskov Substitution - Subtipos deben ser sustituibles
- **I**nterface Segregation - Interfaces específicas > genéricas
- **D**ependency Inversion - Depender de abstracciones, no concreciones

### DRY (Don't Repeat Yourself)

- Minimizar duplicación de código
- Centralizar lógica reutilizable en `app/common/utils/`
- Evitar lógica repetida o implícita

---

## 🏛️ Screaming Architecture

La arquitectura debe comunicar el **propósito del sistema**, no la tecnología.

**❌ Arquitectura centrada en frameworks:**

```
app/
├── models/
├── views/
├── controllers/
└── utils/
```

**✅ Arquitectura centrada en dominio:**

```
app/
├── modules/
│   ├── users/        # "El sistema gestiona usuarios"
│   ├── products/     # "El sistema gestiona productos"
│   └── orders/       # "El sistema gestiona órdenes"
└── common/
```

---

## 📦 Sub-modularización (Estrategia)

### Regla Práctica

- **≤ 3 archivos:** Mantener en un solo nivel
- **> 3 archivos:** Sub-modularizar por sub-contexto funcional

### Ejemplo de Evolución

**Fase 1 - Inicio (2 archivos):**

```
auth/services/
├── __init__.py
└── auth_service.py
```

✅ **OK - Mantener así**

**Fase 2 - Crecimiento (5 archivos):**

```
auth/services/
├── __init__.py
├── login_service.py
├── register_service.py
├── password_service.py
└── session_service.py
```

⚠️ **ALERTA - Considerar sub-modularización**

**Fase 3 - Refactorización:**

```
auth/
├── login/
│   ├── __init__.py
│   ├── login_service.py
│   └── login_schemas.py
├── register/
│   ├── __init__.py
│   ├── register_service.py
│   └── register_schemas.py
└── password/
    ├── __init__.py
    ├── reset_service.py
    └── change_service.py
```

✅ **EXCELENTE - Sub-contextos claros**

### Principios de Sub-contextos

- Representan **capacidades de negocio**, no detalles técnicos
- Cada sub-contexto tiene cohesión interna
- Mínima dependencia entre sub-contextos

---

## 🎨 Design Patterns (Solo con Valor Real)

Todo patrón aplicado debe:

1. Ser explícitamente mencionado
2. Explicar **por qué** se usa y **qué problema** resuelve

### Repository Pattern (con Protocol)

**Problema:** Desacoplar lógica de negocio de detalles de persistencia.

**Solución:**

```python
# domain/repositories/user_repository.py
from typing import Protocol

class UserRepository(Protocol):
    """Contrato para repositorio de usuarios."""

    def find_by_id(self, user_id: int) -> User | None:
        """Buscar usuario por ID."""
        ...

    def find_by_email(self, email: str) -> User | None:
        """Buscar usuario por email."""
        ...

    def save(self, user: User) -> User:
        """Persistir usuario."""
        ...

    def delete(self, user_id: int) -> bool:
        """Eliminar usuario."""
        ...
```

**Ventajas:**

- ✅ Services no conocen SQLAlchemy (desacoplamiento)
- ✅ Fácil testing (mock del Protocol)
- ✅ Cambiar BD sin tocar services

---

### Service Result Pattern

**Problema:** Evitar excepciones para flujos de negocio esperados.

**Solución:**

```python
# common/responses.py
from typing import Generic, TypeVar

T = TypeVar('T')

class ServiceResult(Generic[T]):
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
        return ServiceResult(success=True, data=data, message=message, error_code=0)

    @staticmethod
    def fail(message: str, error_code: int = 1000) -> "ServiceResult[T]":
        return ServiceResult(success=False, message=message, error_code=error_code)
```

**Ventajas:**

- ✅ Sin excepciones para flujos esperados (email duplicado, validación)
- ✅ Códigos de error consistentes
- ✅ Fácil testing de casos de error

---

### Factory Pattern

**Problema:** Creación compleja de objetos con múltiples dependencias.

```python
# domain/factories/user_factory.py
class UserFactory:
    @staticmethod
    def create_from_registration(email: str, name: str, password: str) -> User:
        return User(
            email=email.lower().strip(),
            name=name.strip(),
            password_hash=hash_password(password),
            is_active=False,
            role=UserRole.USER,
        )
```

---

### Strategy Pattern

**Problema:** Múltiples algoritmos intercambiables para la misma operación.

```python
from typing import Protocol

class PricingStrategy(Protocol):
    def calculate_price(self, base_price: float, quantity: int) -> float: ...

class RegularPricing:
    def calculate_price(self, base_price: float, quantity: int) -> float:
        return base_price * quantity

class BulkDiscountPricing:
    def calculate_price(self, base_price: float, quantity: int) -> float:
        if quantity >= 100:
            return base_price * quantity * 0.8
        return base_price * quantity
```

---

## 🔒 Prevención de Dependencias Cíclicas

### Usar Protocol en lugar de ABC

```python
# ❌ Incorrecto (ABC)
from abc import ABC, abstractmethod
class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> User: pass

# ✅ Correcto (Protocol)
from typing import Protocol
class UserRepository(Protocol):
    def save(self, user: User) -> User: ...
```

### Reglas de Importación

1. **Domain** no importa de ninguna capa
2. **Services** importa de domain (entidades, protocols)
3. **Infrastructure** importa de domain (implementa protocols)
4. **REST** importa de services e infrastructure (solo para DI)

---

## 📊 Separation of Concerns

### Services

- Retornan **entidades de dominio** o **ServiceResult[T]**
- **NO** conocen schemas de Pydantic de REST
- **NO** formatean strings para UI

### Presenters / Serializers (en REST)

- Convierten entidades de dominio a DTOs de respuesta
- Aplicar formato, labels, traducciones
- Ubicación: `app/modules/<module>/rest/presenters.py`

---

**Última actualización:** Febrero 2026
**Tokens aproximados:** ~1,200
