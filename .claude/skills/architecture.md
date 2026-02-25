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

**Implementación:**

```python
# infrastructure/repositories/sqlalchemy_user_repository.py
from sqlalchemy.orm import Session

class SQLAlchemyUserRepository:
    """Implementación concreta con SQLAlchemy."""

    def __init__(self, session: Session):
        self.session = session

    def find_by_id(self, user_id: int) -> User | None:
        model = self.session.query(UserModel).filter_by(id=user_id).first()
        return self._to_entity(model) if model else None

    def save(self, user: User) -> User:
        model = self._to_model(user)
        self.session.add(model)
        self.session.commit()
        return self._to_entity(model)

    def _to_entity(self, model: UserModel) -> User:
        """Convertir ORM model a entidad de dominio."""
        return User(id=model.id, email=model.email, name=model.name)

    def _to_model(self, entity: User) -> UserModel:
        """Convertir entidad de dominio a ORM model."""
        return UserModel(id=entity.id, email=entity.email, name=entity.name)
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
    """
    Resultado de operaciones en la capa de servicios.
    Permite manejar éxito/error sin excepciones.
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

**Uso:**

```python
# services/user_service.py
class UserService:
    def create_user(self, email: str, name: str) -> ServiceResult[User]:
        # Validar reglas de negocio
        if existing := self.repo.find_by_email(email):
            return ServiceResult.fail(
                message="El email ya está registrado",
                error_code=1100
            )

        # Crear entidad
        user = User(email=email, name=name)

        # Persistir
        saved_user = self.repo.save(user)

        # Retornar resultado exitoso
        return ServiceResult.ok(
            data=saved_user,
            message="Usuario creado exitosamente"
        )
```

**Ventajas:**

- ✅ Sin excepciones para flujos esperados (email duplicado, validación)
- ✅ Códigos de error consistentes
- ✅ Fácil testing de casos de error

---

### Application Service Pattern

**Problema:** Orquestar múltiples operaciones de dominio.

**Responsabilidades:**

1. Validar datos de entrada
2. Orquestar operaciones de dominio
3. Coordinar transacciones
4. Retornar resultados estructurados

**NO debe:**

- ❌ Contener lógica de negocio compleja (va en entidades de dominio)
- ❌ Acceder directamente a BD (usar repositorios)
- ❌ Formatear respuestas para UI (va en presenters)

```python
# services/order_service.py
class OrderService:
    """
    Servicio de aplicación para gestión de órdenes.
    Orquesta operaciones entre User, Product, Order.
    """

    def __init__(
        self,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
        user_repo: UserRepository
    ):
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.user_repo = user_repo

    def create_order(
        self,
        user_id: int,
        items: list[OrderItemDTO]
    ) -> ServiceResult[Order]:
        # 1. Validar usuario existe
        user = self.user_repo.find_by_id(user_id)
        if not user:
            return ServiceResult.fail("Usuario no encontrado", 1101)

        # 2. Validar productos existen y hay stock
        for item in items:
            product = self.product_repo.find_by_id(item.product_id)
            if not product:
                return ServiceResult.fail(f"Producto {item.product_id} no existe", 1002)
            if product.stock < item.quantity:
                return ServiceResult.fail(f"Stock insuficiente para {product.name}", 1200)

        # 3. Crear orden (lógica de dominio en entidad Order)
        order = Order.create(user_id=user_id, items=items)

        # 4. Reducir stock (operación coordinada)
        for item in items:
            product = self.product_repo.find_by_id(item.product_id)
            product.reduce_stock(item.quantity)
            self.product_repo.save(product)

        # 5. Persistir orden
        saved_order = self.order_repo.save(order)

        return ServiceResult.ok(saved_order, "Orden creada exitosamente")
```

---

### Factory Pattern

**Problema:** Creación compleja de objetos con múltiples dependencias.

**Solución:**

```python
# domain/factories/user_factory.py
class UserFactory:
    """Factory para crear usuarios con validaciones y defaults."""

    @staticmethod
    def create_from_registration(
        email: str,
        name: str,
        password: str
    ) -> User:
        """
        Crear usuario desde registro.
        Aplica: hash de password, email lowercase, estado inicial.
        """
        return User(
            email=email.lower().strip(),
            name=name.strip(),
            password_hash=hash_password(password),
            is_active=False,  # Requiere verificación de email
            role=UserRole.USER,  # Rol por defecto
            created_at=datetime.utcnow()
        )

    @staticmethod
    def create_admin(email: str, name: str, password: str) -> User:
        """Crear usuario administrador."""
        user = UserFactory.create_from_registration(email, name, password)
        user.role = UserRole.ADMIN
        user.is_active = True  # Admin pre-activado
        return user
```

---

### Strategy Pattern

**Problema:** Múltiples algoritmos intercambiables para la misma operación.

**Solución:**

```python
# domain/pricing/pricing_strategy.py
from typing import Protocol

class PricingStrategy(Protocol):
    """Contrato para estrategias de pricing."""

    def calculate_price(self, base_price: float, quantity: int) -> float:
        """Calcular precio final."""
        ...

class RegularPricing:
    """Pricing estándar sin descuentos."""

    def calculate_price(self, base_price: float, quantity: int) -> float:
        return base_price * quantity

class BulkDiscountPricing:
    """Descuento por volumen."""

    def calculate_price(self, base_price: float, quantity: int) -> float:
        if quantity >= 100:
            return base_price * quantity * 0.8  # 20% descuento
        elif quantity >= 50:
            return base_price * quantity * 0.9  # 10% descuento
        return base_price * quantity

# Uso en servicio
class OrderService:
    def __init__(self, pricing: PricingStrategy):
        self.pricing = pricing

    def calculate_total(self, items: list[OrderItem]) -> float:
        return sum(
            self.pricing.calculate_price(item.price, item.quantity)
            for item in items
        )
```

---

## 🔒 Prevención de Dependencias Cíclicas

### Usar Protocol en lugar de ABC

**❌ Incorrecto (ABC):**

```python
from abc import ABC, abstractmethod

class UserRepository(ABC):  # ❌ Puede causar imports circulares
    @abstractmethod
    def save(self, user: User) -> User:
        pass
```

**✅ Correcto (Protocol):**

```python
from typing import Protocol

class UserRepository(Protocol):  # ✅ Duck typing, sin herencia
    def save(self, user: User) -> User: ...
```

### Reglas de Importación

1. **Domain** no importa de ninguna capa
2. **Services** importa de domain (entidades, protocols)
3. **Infrastructure** importa de domain (implementa protocols)
4. **REST** importa de services e infrastructure (solo para DI)

**Imports relativos** solo si rompen ciclos detectados.

---

## 📊 Separation of Concerns

### Services

- Retornan **entidades de dominio** o **ServiceResult[T]**
- Pueden retornar campos derivados de dominio (`remaining_kcal`, `progress_percent`)
- **NO** conocen schemas de Pydantic de REST
- **NO** formatean strings para UI

### Presenters / Serializers (en REST)

- Convierten entidades de dominio a DTOs de respuesta
- Aplican formato, labels, traducciones
- Ubicación: `app/modules/<module>/rest/presenters.py`

**Ejemplo:**

```python
# rest/presenters/user_presenter.py
class UserPresenter:
    """Presenta entidades User como DTOs de REST."""

    @staticmethod
    def to_response(user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            status_label=UserPresenter._format_status(user.is_active),
            role_label=user.role.value.title()
        )

    @staticmethod
    def _format_status(is_active: bool) -> str:
        return "Activo" if is_active else "Inactivo"
```

---

**Última actualización:** Febrero 2026  
**Tokens aproximados:** ~1,200
