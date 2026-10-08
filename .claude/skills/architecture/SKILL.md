---
name: architecture
description: Patrones de diseño y principios usados en Trading AI API. Usar antes de decidir un patrón, aplicar SOLID, sub-modularizar o diseñar el dominio de un módulo. Cubre Screaming Architecture, Repository (ABC/Protocol), ServiceResult real del proyecto, ServiceFactory, Strategy (clientes LLM, canales de alerta, ejecución paper/live) y cómo evitar dependencias cíclicas.
---

# Arquitectura y patrones

## Principios

- **SOLID**, con especial peso en *Single Responsibility* (un servicio = un caso de uso) y *Dependency Inversion* (los servicios dependen de contratos de `domain`).
- **DRY**: lógica reutilizable en `app/common/utils/`, no repetida entre módulos.
- Todo patrón se aplica **solo si resuelve un problema concreto**, y se nombra y justifica al proponerlo.

## Screaming Architecture

La estructura grita *qué hace el sistema*: `app/modules/market`, `bots`, `orders`, `billing`… no `models/`, `views/`, `controllers/`. Las sub-carpetas representan capacidades de negocio (p. ej. `services/strategies/` y `services/datasets/`), no detalles técnicos.

## Repository

**Problema:** desacoplar la lógica de negocio de SQLAlchemy.

- Contrato en `domain/<x>_repository.py`; implementación `SqlAlchemy<X>Repository` en `infrastructure/<x>_repository_impl.py`.
- El repositorio recibe y devuelve **entidades de dominio**, nunca modelos ORM.
- Hereda `SqlAlchemyRepository` (implementación) / `TransactionalRepository` (contrato): es la única capa que toca `session.commit()`. El servicio decide cuándo, llamando `repo.commit()`.
- Contratos: el código existente usa `ABC` (la mayoría) y `Protocol` (alerts, billing). **En código nuevo preferir `typing.Protocol`**; no migrar los ABC existentes salvo que el usuario lo pida.

```python
# domain/strategy_repository.py
class StrategyRepository(TransactionalRepository, Protocol):
    def get_by_id(self, strategy_id: int) -> Strategy | None: ...
    def create(self, strategy: Strategy) -> Strategy: ...
```

## ServiceResult (contrato real: `app/common/contracts/service_result.py`)

**Problema:** los flujos de negocio esperados (duplicado, no encontrado, validación) no deben ser excepciones, y los servicios no deben conocer textos de UI.

```python
from app.common.contracts import ServiceResult

def create(self, ...) -> ServiceResult[Strategy]:
    if self._repo.get_by_name_version(name, version):
        return ServiceResult.fail(code="STRATEGY_DUPLICATE_NAME_VERSION", http_status=409)
    created = self._repo.create(strategy)
    self._repo.commit()
    return ServiceResult.ok(data=created)
```

- `ServiceResult.ok(data)` → `success=True`.
- `ServiceResult.fail(code=..., http_status=..., meta=...)` → `success=False`, `error=ServiceError(...)`.
- `code`: string estable en `SCREAMING_SNAKE_CASE`, prefijado por recurso (`STRATEGY_`, `BOT_`, `ORDER_`…).
- `meta`: datos internos (p. ej. `attempts_left`), **nunca** texto para el usuario.
- El texto lo pone la capa REST con `error_messages.py` (ver skill `api-standards`).

## Factory (ServiceFactory por módulo)

**Problema:** cada servicio necesita varios repositorios, la sesión y a veces clientes externos (cipher, LLM, ccxt).

- Una `<Modulo>ServiceFactory(session)` en `providers/` crea los repositorios una vez y expone un método por servicio.
- Las rutas obtienen la factory con `Depends(get_factory)`.
- En tests se instancia el servicio directamente con mocks; no hace falta la factory.

## Strategy (algoritmos intercambiables)

Ya se usa en tres sitios; seguir el mismo enfoque si aparece otro caso:

| Dónde | Contrato | Implementaciones |
|---|---|---|
| `agent/llm/` | `llm_client.py` | `anthropic_client.py`, `openai_compatible_client.py` (OpenAI, xAI, DeepSeek, Gemini, Ollama); elegido por `llm_factory.py` según `LLM_PROVIDER` |
| `alerts/channels/` | `channel_interface.py` | email, Telegram, webhook, desktop |
| `orders/execution/` | ejecutor | paper (simulado) vs live (ccxt) |

## Evitar dependencias cíclicas

1. `domain` no importa de ninguna capa.
2. `services` importa entidades y contratos de `domain`.
3. `infrastructure` importa de `domain` (implementa contratos).
4. `rest` importa de `providers`/`services` y de `app.common`.
5. Si un módulo necesita datos de otro (p. ej. `bots` usa `strategies` y `features`), depende de su **contrato de dominio**, y el wiring se hace en el provider.

## Separación de responsabilidades

| Capa | Hace | No hace |
|---|---|---|
| Service | Reglas de negocio, orquesta repos, decide cuándo `repo.commit()` | Textos UI, HTTP, schemas Pydantic, `Session` |
| REST | Valida input (Pydantic), autentica, serializa, mensajes UI | Reglas de negocio |
| Repository | Persistencia, mapeo Model ↔ Entity, `commit()`/`rollback()` | Reglas de negocio |
| Entity | Estado + invariantes del dominio (`is_valid_type()`, `is_coherent()`…) | I/O |
