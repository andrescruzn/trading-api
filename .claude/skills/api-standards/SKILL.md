---
name: api-standards
description: Estándares REST de Trading App. Usar antes de crear o modificar endpoints, respuestas, códigos de error o mensajes de UI. Cubre el envelope {msg, errorCode, data}, los helpers build_*_response de app.common.http, el flujo ServiceResult → error_messages.py → JSON, autenticación/roles en rutas, convenciones de URL y paginación.
---

# Estándares de API REST

## Envelope (obligatorio)

Toda respuesta pasa por `app.common.http.send()` (directo o vía `build_*_response`):

```json
{ "msg": "texto para la UI", "errorCode": 201, "data": { } }
```

- `errorCode` **es el HTTP status real** (200, 201, 400, 404, 409, 422, 500…). Nunca 0.
- El frontend detecta error con `errorCode >= 400`.
- `data` nunca es `null`: si no hay datos, `[]`.
- En `send()` el argumento `data` es opcional (por defecto `[]`).

## Helpers (`from app.common.http import ...`)

| Helper | Uso | `data` resultante |
|---|---|---|
| `build_success_response(data, msg="OK", status_code=200)` | GET / PUT / PATCH | el objeto |
| `build_created_response(data, msg)` | POST que crea | el objeto (201) |
| `build_list_response(items, msg="OK")` | Listado simple | **la lista directamente** (`data: [...]`) |
| `build_paginated_response(items, total, page, page_size)` | Listado paginado | `{items, pagination: {total, page, page_size, total_pages}}` |
| `build_data_response(data, datetime_fields=[...])` | Convierte fechas UTC → Bogotá | el objeto |
| `build_error_response(result, ERROR_MESSAGES)` | `ServiceResult` fallido | `[]`, status = `error.http_status` |
| `build_from_service_result(result, ERROR_MESSAGES, transform=...)` | Éxito o error en una llamada | — |
| `build_cookie_auth_response` / `build_logout_response` | Auth con cookie HTTP-only | — |

## Flujo Service → Route

```python
# services/strategies/create_strategy_service.py
return ServiceResult.fail(code="STRATEGY_DUPLICATE_NAME_VERSION", http_status=409)

# rest/strategies/error_messages.py
STRATEGY_ERROR_MESSAGES: dict[str, str] = {
    "STRATEGY_DUPLICATE_NAME_VERSION": "Ya existe una estrategia con ese nombre y versión.",
}

# rest/strategies/routes.py
@router.post("", status_code=201)
def create_strategy(
    payload: CreateStrategyRequest,
    identity: dict = Depends(admin_required),
    factory: StrategyServiceFactory = Depends(get_factory),
):
    result = factory.create_strategy().create(name=payload.name, ...)
    if not result.success:
        return build_error_response(result, STRATEGY_ERROR_MESSAGES)
    return build_created_response(data=_strategy_to_dict(result.data), msg="Estrategia creada exitosamente.")
```

Reglas:
- Un `error_messages.py` por recurso en `rest/<recurso>/`, con **todos** los códigos que puede devolver su servicio. Si falta, el usuario ve el código crudo.
- Mensajes de UI en español, claros y sin detalles internos.
- Serializar entidades con una función `_x_to_dict()` en la ruta o un schema Pydantic; nunca devolver modelos ORM.

## Autenticación y roles en rutas

- Usuario autenticado: `identity: dict = Depends(token_required_actual)` → `identity["user_id"]`, `identity["role_id"]`.
- Solo admin: `Depends(admin_required)` (de `app.common.security.jwt`). Preferirlo a comparar `role_id` a mano dentro de la ruta.
- Recursos de usuario: filtrar siempre por `identity["user_id"]` (ownership) en el servicio.
- Endpoints de auth: `Depends(check_auth_rate_limit)`.

## Códigos HTTP

| Status | Cuándo |
|---|---|
| 200 | GET, PUT, PATCH, acciones OK |
| 201 | POST que crea |
| 400 | Petición mal formada / regla simple |
| 401 | No autenticado (lo gestiona `jwt_guard`) |
| 403 | Autenticado sin permiso / recurso de otro usuario |
| 404 | Recurso no existe |
| 409 | Conflicto (duplicado, estado incompatible) |
| 422 | Validación de negocio fallida (Pydantic también usa 422) |
| 429 | Rate limit |
| 500 | Inesperado (`build_internal_error_response`) |

## URLs

- Prefijo `/api/<recurso>` para toda ruta REST nueva (evita colisión con páginas web homónimas: `/bots` es la página, `/api/bots` la API). Los módulos antiguos (`/users`, `/exchanges`, `/symbols`, `/timeframes`, `/candles`, `/feature-sets`, `/candle-features`, `/accounts`, `/agent`) no lo llevan: no renombrarlos sin que el usuario lo pida (rompe el JS).
- Sustantivos en plural y kebab-case: `/api/managed-accounts`, `/api/model-runs`.
- Sin verbos, salvo acciones no-CRUD justificadas: `POST /api/signals/generate`, `POST /api/bots/{id}/start`.
- Sub-recursos máximo 2 niveles: `/api/accounts/{id}/balances`.
- `tags=[...]` en el `APIRouter` para agrupar en Swagger (`/docs`).

## Prohibido

- ❌ Devolver `ServiceResult` o modelos ORM desde una ruta.
- ❌ `HTTPException` desde services o domain.
- ❌ `errorCode` 0 en éxito.
- ❌ Textos de UI en services.
- ❌ Devolver tokens JWT en el body cuando la sesión va por cookie.
