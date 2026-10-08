---
name: backend-core
description: Estructura real del repo y reglas de capas del backend FastAPI de Trading AI. Usar antes de crear o modificar cualquier módulo, servicio, repositorio, provider o ruta REST. Cubre el árbol de app/, la dirección de dependencias, el wiring con ServiceFactory, los archivos de infraestructura que no se pueden romper y las prohibiciones.
---

# Backend Core — Trading AI API

## Rol y comportamiento

- Explicar qué se va a crear o modificar **antes** de hacerlo y esperar confirmación del usuario.
- Priorizar análisis y propuesta sobre velocidad; proponer mejoras aunque impliquen refactor.
- Antes de crear algo reutilizable, buscar si ya existe en `app/common/` o en otro módulo.

## Estructura real del repo

```
app/
  main.py                    # Entrypoint Uvicorn (app = create_app())
  app_factory.py             # Middlewares, routers, error handlers   ← registrar routers nuevos
  common/
    config/settings.py       # Settings singleton (lee .env, fail-fast fuera de development)
    contracts/service_result.py   # ServiceResult[T], ServiceError
    http/                    # send() + build_*_response()
    errors/                  # register_error_handlers, mensajes globales
    security/                # jwt/ (token_required_actual, admin_required), otp/, rate_limiter,
                             # password_hasher, credentials_cipher, sanitization/, security_headers
    audit/                   # audit middleware + repositorio (audit_logs)
    logging/                 # configure_logging(), LoggingMiddleware
    utils/                   # utc_now(), utc_to_bogota(), clean_email(), clean_str()
  extensions/db/
    base.py                  # class Base(DeclarativeBase)
    session.py               # engine síncrono (UTC) + get_db()
    models_registry.py       # importa TODOS los modelos ORM          ← registrar modelos nuevos
  modules/<modulo>/          # accounts, agent, alerts, billing, bots, features, market,
                             # orders, strategies, users, mailer, health, scheduler, web
  templates/ static/         # Páginas Jinja2 + JS/CSS (ver skill web-ui)
```

### Anatomía de un módulo (ejemplo real: `app/modules/strategies/`)

```
domain/
  strategy_entity.py              # clase Strategy: pura, sin ORM ni FastAPI, con reglas de negocio
  strategy_repository.py          # contrato StrategyRepository(TransactionalRepository, ABC|Protocol)
infrastructure/
  strategy_model.py               # StrategyModel(Base)
  strategy_repository_impl.py     # SqlAlchemyStrategyRepository(SqlAlchemyRepository, ...): Model ↔ Entity
providers/
  strategy_provider.py            # StrategyServiceFactory(session) → un método por servicio
services/
  strategies/                     # un sub-paquete por recurso
    create_strategy_service.py    # CreateStrategyService.create(...) → ServiceResult[Strategy]
    __init__.py                   # barrel export
rest/
  strategies/                     # un sub-paquete por recurso
    routes.py                     # APIRouter(prefix="/api/strategies")
    schemas.py                    # Pydantic request/response
    error_messages.py             # STRATEGY_ERROR_MESSAGES = {code: texto UI}
```

Módulos con piezas extra: `agent/llm/` (clientes LLM por provider), `alerts/channels/` (email, Telegram, webhook, desktop), `orders/execution/` (paper vs live con ccxt).

## Dirección de dependencias

```
rest → providers → services → domain ← infrastructure
```

- `domain` no importa de ninguna otra capa.
- `services` depende de los **contratos** de `domain`, nunca de `infrastructure` ni de `rest`.
- `infrastructure` implementa los contratos de `domain`.
- `providers` es el único sitio que instancia repositorios concretos y servicios.
- `rest` usa la factory vía `Depends` y convierte `ServiceResult` en respuesta HTTP.

## Patrón de wiring (cómo se conecta todo)

```python
# providers/strategy_provider.py
class StrategyServiceFactory:
    def __init__(self, session: Session):
        self._session = session
        self._strategy_repo = SqlAlchemyStrategyRepository(session)

    def create_strategy(self) -> CreateStrategyService:
        return CreateStrategyService(repo=self._strategy_repo)   # el servicio nunca recibe Session

# rest/strategies/routes.py
def get_factory(db: Session = Depends(get_db)) -> StrategyServiceFactory:
    return StrategyServiceFactory(session=db)
```

## Transacciones

- `session.commit()` / `rollback()` existen **solo** en `app/extensions/db/sqlalchemy_repository.py` (`SqlAlchemyRepository`), base de todos los repositorios.
- Todo contrato de dominio hereda `TransactionalRepository` (`app/common/contracts`), que declara `commit()` y `rollback()`.
- Los métodos de escritura del repositorio (`create`, `update`, `save`…) hacen `add` / `flush`, sin commit.
- El **servicio** decide *cuándo* confirmar: `self._repo.commit()` al final del caso de uso, o `self._repo.rollback()` si algo falla a mitad. **Nunca** recibe ni usa `Session`.
- Todos los repositorios de un request comparten la sesión: un solo `commit()` confirma las escrituras de varios repos de forma atómica (p. ej. order + fill + position en `CreateOrderService`).
- Procesos fuera de request (scheduler) abren su `SessionLocal()`, construyen repos con ella y confirman con `repo.commit()`.

## Prohibiciones

- ❌ Imports cíclicos entre módulos; ❌ importar desde `rest` hacia capas internas.
- ❌ Modelos ORM como respuesta REST: serializar la entidad (`_x_to_dict` o schema Pydantic).
- ❌ Textos de UI, labels o formato en services.
- ❌ Services que conozcan schemas Pydantic de `rest`.
- ❌ Lógica de negocio en endpoints.
- ❌ Helpers reutilizables dentro de `services/`: van a `app/common/utils/`.
- ❌ Código muerto o duplicado.

## Sub-modularización

- ≤ 3 archivos en una carpeta → un solo nivel.
- > 3 archivos → sub-paquetes por recurso o capacidad de negocio (como `services/strategies/`, `services/datasets/`).
- Cada paquete expone su API en `__init__.py` (barrel export con `__all__`).

## Archivos de infraestructura críticos (nunca romper)

| Archivo | Cuándo tocarlo |
|---|---|
| `app/extensions/db/models_registry.py` | Modelo ORM nuevo |
| `app/app_factory.py` | Router nuevo |
| `app/modules/web/routes.py` | Página web nueva |
| `app/common/security/security_headers.py` | Prefijo web nuevo → `_is_web_route()` |
| `app/extensions/db/session.py` | `get_db()`; no cambiar sin motivo |
| `app/common/contracts/service_result.py` | Contrato de todos los servicios |
| `app/common/http/response_builder.py` | Helpers de respuesta |

## Carpetas a ignorar

`.venv/`, `__pycache__/`, `.git/`, `.env`, `instance/`, `uv.lock`, `.pytest_cache/`. Foco en `app/`, `tests/`, `seeds/`, `alembic/`, `specs/`.

## Relacionados

- Crear un módulo completo: skill `new-module`.
- Patrones y ServiceResult a fondo: skill `architecture`.
- Respuestas y códigos de error: skill `api-standards`.
