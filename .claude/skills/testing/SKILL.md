---
name: testing
description: Testing standards for this project. Use before writing tests. Covers pytest setup, test pyramid, fixture structure, unit tests with mocks, integration tests with DB and endpoints, coverage goals, and anti-patterns to avoid.
---

# Testing Standards & Best Practices

## ⚠️ Reglas de ejecución de tests (LEER PRIMERO)

- **SOLO ejecutar los tests del archivo/servicio que se creó o modificó.**
- NO correr `pytest tests/` completo salvo que el usuario lo pida explícitamente.
- Ejemplo: si se modificó `get_me_service.py` → correr `pytest tests/users/test_get_me_service.py -v`
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
│   ├── domain/
│   └── services/
├── integration/                   # Tests de integración (con DB, APIs)
│   ├── repositories/
│   └── endpoints/
└── e2e/                          # Tests end-to-end (flujos completos)
```

---

## 🔧 Fixtures y Conftest

```python
# tests/conftest.py
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    engine.sync_engine.dispose()

@pytest.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

---

## 📝 Unit Tests (Sin I/O)

```python
# tests/unit/services/test_user_service.py
import pytest
from unittest.mock import MagicMock
from app.modules.users.services import UserService
from app.modules.users.domain.entities import User
from app.common.error_codes import ErrorCode

class TestUserService:
    @pytest.fixture
    def service(self, mock_user_repository):
        return UserService(repository=mock_user_repository)

    def test_create_user_success(self, service, mock_user_repository):
        # Arrange
        mock_user_repository.find_by_email.return_value = None
        mock_user_repository.save.return_value = User(id=1, email="test@example.com", name="Test User")
        # Act
        result = service.create_user(email="test@example.com", name="Test User")
        # Assert
        assert result.success is True
        assert result.data.id == 1
        assert result.error_code == ErrorCode.SUCCESS

    def test_create_user_fails_if_email_exists(self, service, mock_user_repository):
        # Arrange
        mock_user_repository.find_by_email.return_value = User(id=1, email="test@example.com", name="Existing")
        # Act
        result = service.create_user(email="test@example.com", name="Test User")
        # Assert
        assert result.success is False
        assert result.error_code == ErrorCode.USER_EMAIL_EXISTS
        mock_user_repository.save.assert_not_called()
```

---

## 🌐 Integration Tests (Endpoints)

```python
@pytest.mark.integration
class TestUsersEndpoints:
    @pytest.mark.asyncio
    async def test_create_user_success(self, client: AsyncClient):
        payload = {"email": "newuser@example.com", "name": "New User", "password": "SecurePass123"}
        response = await client.post("/api/v1/users", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["errorCode"] == ErrorCode.SUCCESS
        assert data["data"]["email"] == "newuser@example.com"
```

---

## 📊 Coverage Goals

```
Tipo de Código              | Coverage Mínimo
----------------------------|----------------
Domain (entities)           | 90%
Services (business logic)   | 80%
Repositories                | 70%
Utils                       | 80%
REST endpoints              | 60%
```

---

## 🎯 Best Practices

### AAA Pattern (Arrange-Act-Assert)

```python
def test_user_creation():
    # Arrange - Preparar datos de prueba
    email = "test@example.com"
    # Act - Ejecutar acción
    user = User(email=email, name="Test")
    # Assert - Verificar resultado
    assert user.email == email
```

### Nombres Descriptivos

```python
# ✅ BIEN
def test_create_user_fails_if_email_already_exists(): pass

# ❌ MAL
def test_user(): pass
```

---

## 🚫 Anti-Patterns

```python
# ❌ MAL - Test de implementación (CÓMO, no QUÉ)
def test_user_service_calls_repository():
    service.create_user(...)
    mock_repo.save.assert_called_once()

# ✅ BIEN - Test de comportamiento
def test_create_user_persists_user_data():
    result = service.create_user(...)
    assert result.success is True
    assert result.data.email == "test@example.com"
```

---

**Última actualización:** Febrero 2026
**Tokens aproximados:** ~600
