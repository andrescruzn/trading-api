---
name: testing
description: Estándares de tests de Trading AI API. Usar SOLO cuando el usuario pida explícitamente escribir o ejecutar tests. Cubre qué tests correr (nunca la suite completa), estructura real tests/<modulo>/test_<servicio>.py, tests unitarios de servicios con MagicMock, tests de rutas web con TestClient, fixtures de conftest y anti-patrones.
---

# Testing

## Reglas de ejecución (leer primero)

- **No crear tests si el usuario no los pidió**: gastan tokens y tiempo.
- **Ejecutar solo el archivo afectado**: `uv run python -m pytest tests/<modulo>/test_<x>.py -v`.
- **NUNCA** `pytest tests/` completo salvo petición explícita.
- Si un test falla, reportarlo con la salida real; no "arreglar" el test para que pase sin entender por qué falla.

## Estructura real

```
tests/
  conftest.py              # app, client (TestClient), make_user(), make_mock_repo(), mock_session
  <modulo>/                # accounts, agent, billing, bots, features, users, web, common/audit
    test_<x>_service.py    # unitarios de un servicio
    test_<x>_entity.py     # reglas de una entidad de dominio
  web/test_web_routes.py   # redirecciones y páginas con TestClient
```

Módulos **sin tests** hoy (prioridad alta en `specs/_ROOT.md`): market, strategies, orders, alerts.

## Test unitario de servicio (patrón del repo)

Sin BD: el servicio se instancia con repositorios `MagicMock` (los servicios no reciben `Session`).

```python
# tests/strategies/test_create_strategy_service.py
from unittest.mock import MagicMock

from app.modules.strategies.domain.strategy_entity import Strategy
from app.modules.strategies.services.strategies.create_strategy_service import CreateStrategyService


def _make_service(existing: Strategy | None = None):
    repo = MagicMock()
    repo.get_by_name_version.return_value = existing
    repo.create.side_effect = lambda s: s
    return CreateStrategyService(repo=repo), repo


class TestCreateStrategyService:

    def test_fails_with_409_when_name_version_exists(self):
        svc, repo = _make_service(existing=MagicMock())

        result = svc.create(name="X", version="1.0.0", parameters={})

        assert result.success is False
        assert result.error.code == "STRATEGY_DUPLICATE_NAME_VERSION"
        assert result.error.http_status == 409
        repo.commit.assert_not_called()
```

Qué verificar:
- Éxito: `result.success`, `result.data`, y que se hizo `repo.commit()`.
- Error: `result.error.code` y `result.error.http_status`; que **no** se hizo `repo.commit()`.
- Reglas de trading con números concretos (tamaño de posición, R:R ≥ 2, regla del 1 %).

## Test de rutas

```python
@pytest.fixture(scope="module")
def client():
    with TestClient(create_app(), raise_server_exceptions=False, follow_redirects=False) as c:
        yield c

def test_root_redirects_to_login_without_cookie(client):
    res = client.get("/")
    assert res.status_code in (301, 302)
```

- En JSON, verificar el envelope: `res.json()["errorCode"]` igual al status HTTP.
- No hacer login real contra la BD (rota `token_current_jti`).

## Buenas prácticas

- Arrange / Act / Assert, un comportamiento por test.
- Nombres descriptivos: `test_rejects_signal_when_rr_below_2`.
- Helpers `_make_<x>()` locales al archivo para construir entidades y servicios.
- Probar **comportamiento** (resultado, estado) por encima de detalles de implementación; los `assert_called` solo para efectos que importan (commit, envío de alerta, orden al exchange).
- Nunca llamar a exchanges ni LLMs reales: mockear el cliente ccxt / LLM.
