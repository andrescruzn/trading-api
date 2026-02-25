# Testing Standards & Best Practices

## ⚠️ Reglas de ejecución de tests (LEER PRIMERO)

- **SOLO ejecutar los tests del archivo/servicio que se creó o modificó.**
- NO correr `pytest tests/` completo salvo que el usuario lo pida explícitamente.
- Ejemplo: si se modificó `get_me_service.py` → correr `pytest tests/users/test_get_me_service.py -v`
- Ejemplo: si se creó un nuevo servicio → crear su test y correlo solo.
- Ejecutar toda la suite consume tiempo y no aporta valor en cambios puntuales.

---

## 🎯 Testing Strategy

### Pirámide de Testing

```
        /\
       /  \        E2E (pocos)
      /____\
     /      \      Integration (algunos)
    /________\
   /          \    Unit (muchos)
  /__________\
```

**Distribución recomendada:**

- **70%** Unit tests (lógica de negocio, utils, domain)
- **20%** Integration tests (repositorios, endpoints)
- **10%** E2E tests (flujos completos)

---

## 📁 Estructura de Tests

```
tests/
├── __init__.py
├── conftest.py                    # Fixtures compartidas
├── unit/                          # Tests unitarios (sin I/O, sin DB)
│   ├── __init__.py
│   ├── domain/
│   │   ├── test_user_entity.py
│   │   └── test_order_entity.py
│   ├── services/
│   │   ├── test_user_service.py
│   │   └── test_order_service.py
│   └── utils/
│       ├── test_validators.py
│       └── test_formatters.py
├── integration/                   # Tests de integración (con DB, APIs)
│   ├── __init__.py
│   ├── repositories/
│   │   ├── test_user_repository.py
│   │   └── test_order_repository.py
│   └── endpoints/
│       ├── test_users_endpoints.py
│       └── test_orders_endpoints.py
└── e2e/                          # Tests end-to-end (flujos completos)
    ├── __init__.py
    └── test_user_registration_flow.py
```

---

## 🧪 Pytest Configuration

### `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# Markers para categorizar tests
markers = [
    "unit: Unit tests (no I/O, no DB)",
    "integration: Integration tests (with DB, external services)",
    "e2e: End-to-end tests (full workflows)",
    "slow: Tests that take > 1 second",
]

# Asyncio
asyncio_mode = "auto"

# Coverage
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",  # Show summary of all test outcomes
]
```

### Comandos

```bash
# Ejecutar todos los tests
pytest

# Solo unit tests
pytest -m unit

# Solo integration tests
pytest -m integration

# Con coverage
pytest --cov=app --cov-report=term-missing

# Con coverage y HTML report
pytest --cov=app --cov-report=html

# Tests específicos
pytest tests/unit/services/test_user_service.py

# Test específico por nombre
pytest -k "test_create_user_success"

# Modo verbose
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s
```

---

## 🔧 Fixtures y Conftest

### `conftest.py` (Global)

```python
# tests/conftest.py
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

# ======================================================================
# Database Fixtures
# ======================================================================

# Motor de test (in-memory SQLite o PostgreSQL test)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    """Motor de BD para tests."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    engine.sync_engine.dispose()


@pytest.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Sesión de BD con rollback automático.
    Cada test tiene su propia sesión aislada.
    """
    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Crear sesión
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    # Limpiar tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ======================================================================
# HTTP Client Fixtures
# ======================================================================

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP para tests de endpoints.
    Usa la sesión de BD de test.
    """
    # Override de dependencia de DB
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ======================================================================
# Mock Fixtures
# ======================================================================

@pytest.fixture
def mock_user_repository():
    """Mock de UserRepository para unit tests."""
    from unittest.mock import MagicMock
    from app.modules.users.domain.repositories import UserRepository

    mock_repo = MagicMock(spec=UserRepository)
    return mock_repo
```

---

## 📝 Unit Tests (Sin I/O)

### Test de Entidad de Dominio

```python
# tests/unit/domain/test_user_entity.py
import pytest
from app.modules.users.domain.entities import User, UserRole

class TestUserEntity:
    """Tests para la entidad User."""

    def test_create_user_success(self):
        """Debe crear usuario con datos válidos."""
        # Arrange & Act
        user = User(
            id=1,
            email="test@example.com",
            name="Test User",
            role=UserRole.USER
        )

        # Assert
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.role == UserRole.USER
        assert user.is_active is True  # Default

    def test_email_normalized_to_lowercase(self):
        """Debe normalizar email a lowercase."""
        # Arrange & Act
        user = User(
            id=1,
            email="TEST@EXAMPLE.COM",
            name="Test User"
        )

        # Assert
        assert user.email == "test@example.com"

    def test_is_admin_returns_true_for_admin_role(self):
        """Debe retornar True si el usuario es admin."""
        # Arrange
        admin = User(id=1, email="admin@test.com", role=UserRole.ADMIN)
        regular = User(id=2, email="user@test.com", role=UserRole.USER)

        # Act & Assert
        assert admin.is_admin() is True
        assert regular.is_admin() is False
```

### Test de Service con Mock

```python
# tests/unit/services/test_user_service.py
import pytest
from unittest.mock import MagicMock
from app.modules.users.services import UserService
from app.modules.users.domain.entities import User
from app.common.error_codes import ErrorCode

class TestUserService:
    """Tests para UserService."""

    @pytest.fixture
    def service(self, mock_user_repository):
        """Fixture de servicio con repo mockeado."""
        return UserService(repository=mock_user_repository)

    def test_create_user_success(self, service, mock_user_repository):
        """Debe crear usuario exitosamente si email no existe."""
        # Arrange
        mock_user_repository.find_by_email.return_value = None  # Email disponible
        mock_user_repository.save.return_value = User(
            id=1,
            email="test@example.com",
            name="Test User"
        )

        # Act
        result = service.create_user(
            email="test@example.com",
            name="Test User"
        )

        # Assert
        assert result.success is True
        assert result.data.id == 1
        assert result.data.email == "test@example.com"
        assert result.error_code == ErrorCode.SUCCESS
        mock_user_repository.find_by_email.assert_called_once_with("test@example.com")
        mock_user_repository.save.assert_called_once()

    def test_create_user_fails_if_email_exists(self, service, mock_user_repository):
        """Debe fallar si el email ya existe."""
        # Arrange
        existing_user = User(id=1, email="test@example.com", name="Existing")
        mock_user_repository.find_by_email.return_value = existing_user

        # Act
        result = service.create_user(
            email="test@example.com",
            name="Test User"
        )

        # Assert
        assert result.success is False
        assert result.error_code == ErrorCode.USER_EMAIL_EXISTS
        assert "ya está registrado" in result.message
        mock_user_repository.save.assert_not_called()
```

---

## 🔌 Integration Tests (Con DB)

### Test de Repository

```python
# tests/integration/repositories/test_user_repository.py
import pytest
from app.modules.users.infrastructure.repositories import SQLAlchemyUserRepository
from app.modules.users.domain.entities import User

@pytest.mark.integration
class TestUserRepository:
    """Tests de integración para UserRepository."""

    @pytest.fixture
    def repository(self, db_session):
        """Fixture de repositorio con sesión real."""
        return SQLAlchemyUserRepository(session=db_session)

    @pytest.mark.asyncio
    async def test_save_and_find_by_id(self, repository):
        """Debe guardar y recuperar usuario por ID."""
        # Arrange
        user = User(email="test@example.com", name="Test User")

        # Act
        saved_user = await repository.save(user)
        found_user = await repository.find_by_id(saved_user.id)

        # Assert
        assert found_user is not None
        assert found_user.id == saved_user.id
        assert found_user.email == "test@example.com"
        assert found_user.name == "Test User"

    @pytest.mark.asyncio
    async def test_find_by_email_returns_none_if_not_exists(self, repository):
        """Debe retornar None si email no existe."""
        # Act
        result = await repository.find_by_email("nonexistent@example.com")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_user(self, repository):
        """Debe eliminar usuario exitosamente."""
        # Arrange
        user = User(email="test@example.com", name="Test User")
        saved_user = await repository.save(user)

        # Act
        deleted = await repository.delete(saved_user.id)
        found_user = await repository.find_by_id(saved_user.id)

        # Assert
        assert deleted is True
        assert found_user is None
```

---

## 🌐 Integration Tests (Endpoints)

### Test de Endpoint con httpx

```python
# tests/integration/endpoints/test_users_endpoints.py
import pytest
from httpx import AsyncClient
from app.common.error_codes import ErrorCode

@pytest.mark.integration
class TestUsersEndpoints:
    """Tests de integración para endpoints de usuarios."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, client: AsyncClient):
        """POST /users debe crear usuario exitosamente."""
        # Arrange
        payload = {
            "email": "newuser@example.com",
            "name": "New User",
            "password": "SecurePass123"
        }

        # Act
        response = await client.post("/api/v1/users", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["errorCode"] == ErrorCode.SUCCESS
        assert data["msg"] == "Usuario creado exitosamente"
        assert data["data"]["email"] == "newuser@example.com"
        assert "id" in data["data"]

    @pytest.mark.asyncio
    async def test_create_user_fails_if_email_exists(self, client: AsyncClient):
        """POST /users debe fallar si email ya existe."""
        # Arrange - Crear usuario primero
        payload = {
            "email": "duplicate@example.com",
            "name": "First User",
            "password": "Password123"
        }
        await client.post("/api/v1/users", json=payload)

        # Act - Intentar crear con mismo email
        response = await client.post("/api/v1/users", json=payload)

        # Assert
        assert response.status_code == 200  # No 4xx, error en data
        data = response.json()
        assert data["errorCode"] == ErrorCode.USER_EMAIL_EXISTS
        assert "ya está registrado" in data["msg"]

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, client: AsyncClient):
        """GET /users debe retornar lista paginada."""
        # Arrange - Crear varios usuarios
        for i in range(5):
            await client.post("/api/v1/users", json={
                "email": f"user{i}@example.com",
                "name": f"User {i}",
                "password": "Pass123"
            })

        # Act
        response = await client.get("/api/v1/users?page=1&limit=3")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["errorCode"] == ErrorCode.SUCCESS
        assert len(data["data"]["items"]) == 3
        assert data["data"]["paginate"]["page"] == 1
        assert data["data"]["paginate"]["limit"] == 3
        assert data["data"]["paginate"]["total"] == 5
```

---

## 📊 Coverage Goals

### Mínimos Requeridos

```
Tipo de Código              | Coverage Mínimo
----------------------------|----------------
Domain (entities)           | 90%
Services (business logic)   | 80%
Repositories                | 70%
Utils                       | 80%
REST endpoints              | 60%
```

### Comando de Coverage

```bash
# Generar reporte
pytest --cov=app --cov-report=term-missing

# Con HTML
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Fallar si coverage < 70%
pytest --cov=app --cov-fail-under=70
```

---

## 🎯 Best Practices

### AAA Pattern (Arrange-Act-Assert)

```python
def test_user_creation():
    # Arrange - Preparar datos de prueba
    email = "test@example.com"
    name = "Test User"

    # Act - Ejecutar acción
    user = User(email=email, name=name)

    # Assert - Verificar resultado
    assert user.email == email
    assert user.name == name
```

### Nombres Descriptivos

```python
# ✅ BIEN
def test_create_user_fails_if_email_already_exists():
    pass

def test_calculate_discount_returns_zero_for_regular_customers():
    pass

# ❌ MAL
def test_user():
    pass

def test_discount():
    pass
```

### Un Assert por Concepto

```python
# ✅ BIEN - Múltiples asserts relacionados
def test_user_creation():
    user = User(email="test@example.com", name="Test")
    assert user.email == "test@example.com"
    assert user.name == "Test"
    assert user.is_active is True

# ❌ EVITAR - Múltiples conceptos no relacionados
def test_everything():
    # Test creación
    user = User(...)
    assert user.id == 1

    # Test update (debería ser test separado)
    user.name = "Updated"
    assert user.name == "Updated"

    # Test delete (debería ser test separado)
    deleted = repo.delete(user.id)
    assert deleted is True
```

---

## 🚫 Anti-Patterns

### ❌ Testing Implementation Details

```python
# ❌ MAL - Test de implementación
def test_user_service_calls_repository():
    # No testear CÓMO se hace, sino QUÉ se logra
    service.create_user(...)
    mock_repo.save.assert_called_once()

# ✅ BIEN - Test de comportamiento
def test_create_user_persists_user_data():
    result = service.create_user(...)
    assert result.success is True
    assert result.data.email == "test@example.com"
```

### ❌ Tests Interdependientes

```python
# ❌ MAL - Test depende de orden
class TestUser:
    user_id = None

    def test_create_user(self):
        user = create_user()
        TestUser.user_id = user.id  # Estado compartido

    def test_update_user(self):
        update_user(TestUser.user_id)  # Depende del anterior

# ✅ BIEN - Tests independientes
class TestUser:
    @pytest.fixture
    def created_user(self):
        return create_user()

    def test_update_user(self, created_user):
        update_user(created_user.id)
```

---

**Última actualización:** Febrero 2026  
**Tokens aproximados:** ~600
