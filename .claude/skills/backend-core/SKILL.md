---
name: backend-core
description: Python/FastAPI backend standards for this project. Use before creating any module, service, repository, or REST endpoint. Covers project structure (Screaming Architecture), layer rules (domain→infra→service→rest), dependency direction, and prohibitions.
---

# Backend Core Standards (Python/FastAPI)

## 🎯 Role & Behavior

Asistente técnico **crítico y disciplinado** para backend Python (FastAPI).

**Reglas de Interacción:**

- ❌ **NUNCA** modificar ni borrar archivos sin explicar primero qué va a cambiar
- ❌ **NUNCA** aplicar cambios sin confirmación explícita del usuario
- ✅ Priorizar **análisis, propuesta y control** sobre velocidad
- ✅ Proponer mejoras sin filtro, incluso si implican refactorizaciones

---

## 🏗️ Project Structure (Screaming Architecture)

La estructura debe "gritar" **qué hace el sistema**, no qué tecnología usa.

```
app/
├── main.py                          # FastAPI app
├── core/
│   ├── __init__.py
│   └── config.py                    # Settings (Pydantic v2)
├── common/
│   ├── __init__.py
│   ├── utils/                       # ✅ Funciones reutilizables
│   ├── error_codes.py               # Catálogo de códigos de error
│   └── responses.py                 # ApiResponse, ServiceResult
└── modules/
    └── <module_name>/               # Ej: users, products, orders
        ├── __init__.py
        ├── domain/                  # Entidades, Protocols (contratos)
        ├── infrastructure/          # Repositorios, DB, externos
        ├── services/                # Lógica de negocio
        └── rest/                    # Endpoints, schemas (Pydantic)
```

---

## 🧭 Dependency Direction (Estricta)

```
rest → services → domain ← infrastructure
       ↓              ↑
   (orchestration)  (contracts via Protocol)
```

**Reglas:**

- `rest` depende de `services` e `infrastructure` (solo para inyección)
- `services` depende de `domain` e `infrastructure` (vía contratos Protocol)
- `infrastructure` implementa contratos y depende de `domain`
- `domain` **NO depende de ninguna otra capa** (núcleo puro)

---

## 🚫 Prohibiciones Críticas

### Dependencias Cíclicas

- ❌ Imports cíclicos entre módulos
- ❌ Usar ABCs para contratos (usar `Protocol` de `typing`)
- ❌ Importar desde `rest` hacia capas internas

### Código Innecesario

- ❌ Código muerto, duplicado o sin propósito claro
- ❌ Utils/helpers definidos dentro de `services`
- ❌ Modelos ORM (SQLAlchemy) como respuesta directa en REST
- ❌ Formato/presentación (labels, strings UI) dentro de services

### Separación de Responsabilidades

- ❌ Services conociendo schemas de Pydantic de la capa REST
- ❌ Helpers locales (funciones anidadas) en services sin justificación
- ❌ Lógica de negocio en endpoints REST

---

## ✅ Reglas Obligatorias

### 1. Reutilización Centralizada

Toda lógica reutilizable debe ir en:

```
app/common/utils/
```

**Servicios** solo orquestan lógica de negocio.

### 2. Sub-modularización Automática

- **≤ 3 archivos:** Mantener en un solo nivel
- **> 3 archivos:** Sub-modularizar por contexto funcional

```
# ❌ ANTES - Difícil de navegar
auth/services/
├── login_service.py
├── logout_service.py
├── register_service.py
├── reset_password_service.py
└── (más archivos...)

# ✅ DESPUÉS - Sub-contextos claros
auth/
├── login/
│   ├── __init__.py
│   ├── login_service.py
│   └── login_schemas.py
├── register/
│   ├── __init__.py
│   ├── register_service.py
│   └── register_schemas.py
└── session/
    ├── __init__.py
    └── session_service.py
```

### 3. Barrel Exports (`__init__.py`)

Cada paquete expone una API clara mediante `__init__.py`:

```python
# app/modules/users/services/__init__.py
from .user_service import UserService
from .auth_service import AuthService

__all__ = ["UserService", "AuthService"]
```

**Preferir:**

```python
from app.modules.users.services import UserService
```

**Evitar:**

```python
from app.modules.users.services.user_service import UserService
```

---

## 🔍 Before Creating Code (Checklist)

Antes de crear código reutilizable, Claude debe:

1. **Revisar estructura existente:**
   - `app/common/utils/` - Utils transversales
   - `app/modules/<modulo>/services/` - Servicios de dominio
   - `app/modules/<modulo>/rest/` - Presenters/Schemas

2. **Evaluar sub-modularización:**
   - Si una carpeta tiene >3 archivos, proponer sub-división

3. **Confirmar con usuario:**
   - Explicar qué va a crear/modificar
   - Esperar aprobación explícita

---

## 🛠️ Tech Stack

- **Python:** ≥ 3.10
- **FastAPI:** ≥ 0.110
- **Pydantic:** v2.6+ (Settings, BaseModel)
- **Linter/Formatter:** `ruff` (reemplaza black, isort, flake8)
- **Type Checker:** `mypy --strict`
- **Testing:** `pytest` + `pytest-asyncio`

---

## 🗂️ Carpetas a Ignorar

Claude debe ignorar completamente (salvo indicación explícita):

```
venv/, .venv/, __pycache__/, *.pyc, .git/, .idea/, .vscode/
node_modules/, dist/, build/, *.egg-info/, migrations/, alembic/
logs/, *.log, .env, .coverage, .pytest_cache/, .mypy_cache/
```

**Enfoque exclusivo:** Código fuente en `app/` y `tests/`.

---

**Última actualización:** Febrero 2026
**Tokens aproximados:** ~1,500
