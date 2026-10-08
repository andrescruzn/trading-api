---
name: new-module
description: Checklist de punta a punta para crear un módulo nuevo (o un recurso nuevo dentro de un módulo) en Trading App, desde la spec y la tabla hasta la ruta REST, la página web y la documentación. Usar cuando el usuario pida un módulo o recurso nuevo, o una feature que necesite tabla + servicio + endpoint.
argument-hint: "[nombre del módulo o recurso]"
---

# Crear un módulo o recurso nuevo

Trabajo para: **$ARGUMENTS**

## 0. Antes de escribir código

1. Leer [`specs/_ROOT.md`](../../../specs/_ROOT.md) (orden de dependencias, prioridades) y la spec del módulo `specs/MNN-*.md`. Si el módulo no tiene spec, crearla primero con la plantilla de `_ROOT.md` → "Plantilla de spec".
2. Revisar un módulo hermano ya terminado como referencia (p. ej. `app/modules/strategies/`).
3. Cargar los skills `backend-core`, `code-style` y, según toque, `database`, `api-standards`, `security`, `frontend`.
4. Presentar al usuario el plan (tablas, archivos, endpoints, páginas) y esperar su confirmación.

## 1. Base de datos

- [ ] Modelo ORM en `infrastructure/` + registro en `models_registry.py`.
- [ ] Revisión de Alembic generada por el usuario (`alembic revision --autogenerate -m "mNN ..."`), luego revisada y completada a mano (CHECKs, nombres, `downgrade`). Flujo en el skill `database`.
- [ ] Seed idempotente `database/seeds/<dominio>.py` registrado en `database/seeds/__main__.py`, si hay datos de catálogo o de ejemplo (reglas en el skill `database`).
- [ ] Dar al usuario los comandos (`alembic upgrade head`, `python -m database.seeds <dominio>`) y esperar; no ejecutar contra su BD.

## 2. Domain — `app/modules/<modulo>/domain/`

- [ ] `<x>_entity.py`: clase pura con estado e invariantes de negocio (métodos `is_valid_*()`, etc.).
- [ ] `<x>_repository.py`: contrato que hereda `TransactionalRepository` (`Protocol` en código nuevo).
- [ ] `__init__.py` con barrel export.

## 3. Infrastructure — `app/modules/<modulo>/infrastructure/`

- [ ] `<x>_model.py`: `class <X>Model(Base)` con columnas idénticas a la migración.
- [ ] `<x>_repository_impl.py`: `SqlAlchemy<X>Repository(SqlAlchemyRepository, <X>Repository)`, mapea Model ↔ Entity; las escrituras hacen `add`/`flush`.
- [ ] Registrar el modelo en `app/extensions/db/models_registry.py`.

## 4. Services — `app/modules/<modulo>/services/<recurso>/`

- [ ] Un archivo por caso de uso: `<verbo>_<recurso>_service.py` → `ServiceResult[T]`.
- [ ] Códigos de error `<RECURSO>_<MOTIVO>` con su `http_status`; `self._repo.commit()` al final del caso de uso. El servicio **no** recibe `Session`.
- [ ] Ownership: filtrar por `user_id` cuando el recurso pertenece a un usuario.

## 5. Providers — `app/modules/<modulo>/providers/<modulo>_provider.py`

- [ ] `<Modulo>ServiceFactory(session)` con un método por servicio.

## 6. REST — `app/modules/<modulo>/rest/<recurso>/`

- [ ] `schemas.py` (Pydantic v2), `error_messages.py` (todos los códigos del servicio), `routes.py` (`APIRouter(prefix="/<recurso>")`; el `/api` lo añade `app_factory.py`).
- [ ] Auth: `token_required_actual` / `admin_required`.
- [ ] Registrar el router en `app/app_factory.py`.

## 7. Frontend (si el módulo tiene pantallas)

- [ ] Seguir el checklist del skill `frontend`: `modules/<x>/api` → `hooks` → `pages`, ruta fina en `frontend/src/routes/_app/...`, item en `app-sidebar.tsx`, `npm run check-types`.

## 8. Verificar

- [ ] Arrancar el servidor (`uv run uvicorn app.main:app --reload`) y comprobar que importa sin errores.
- [ ] Probar los endpoints en Swagger (`/docs`) con la sesión del navegador. **No** hacer login con `curl`.
- [ ] Tests solo si el usuario los pide (skill `testing`).

## 9. Documentar

- [ ] Ejecutar el skill `update-specs`.
