---
name: new-module
description: Checklist de punta a punta para crear un módulo nuevo (o un recurso nuevo dentro de un módulo) en Trading AI API, desde la spec y la tabla hasta la ruta REST, la página web y la documentación. Usar cuando el usuario pida un módulo o recurso nuevo, o una feature que necesite tabla + servicio + endpoint.
argument-hint: "[nombre del módulo o recurso]"
---

# Crear un módulo o recurso nuevo

Trabajo para: **$ARGUMENTS**

## 0. Antes de escribir código

1. Leer [`specs/_ROOT.md`](../../../specs/_ROOT.md) (orden de dependencias, prioridades) y la spec del módulo `specs/MNN-*.md`. Si el módulo no tiene spec, crearla primero con la plantilla de `_ROOT.md` → "Plantilla de spec".
2. Revisar un módulo hermano ya terminado como referencia (p. ej. `app/modules/strategies/`).
3. Cargar los skills `backend-core`, `code-style` y, según toque, `database`, `api-standards`, `security`, `web-ui`.
4. Presentar al usuario el plan (tablas, archivos, endpoints, páginas) y esperar su confirmación.

## 1. Base de datos

- [ ] Migración `migrations/mNN_<descripcion>.sql` (convenciones en skill `database`).
- [ ] Seed idempotente `seeds/seed_<modulo>.sql` si hay datos de catálogo o de ejemplo.
- [ ] Dar al usuario el comando para ejecutarlos (no ejecutar contra su BD sin permiso).

## 2. Domain — `app/modules/<modulo>/domain/`

- [ ] `<x>_entity.py`: clase pura con estado e invariantes de negocio (métodos `is_valid_*()`, etc.).
- [ ] `<x>_repository.py`: contrato (`Protocol` en código nuevo).
- [ ] `__init__.py` con barrel export.

## 3. Infrastructure — `app/modules/<modulo>/infrastructure/`

- [ ] `<x>_model.py`: `class <X>Model(Base)` con columnas idénticas a la migración.
- [ ] `<x>_repository_impl.py`: `SqlAlchemy<X>Repository`, mapea Model ↔ Entity, `add`/`flush`, **sin commit**.
- [ ] Registrar el modelo en `app/extensions/db/models_registry.py`.

## 4. Services — `app/modules/<modulo>/services/<recurso>/`

- [ ] Un archivo por caso de uso: `<verbo>_<recurso>_service.py` → `ServiceResult[T]`.
- [ ] Códigos de error `<RECURSO>_<MOTIVO>` con su `http_status`; `commit()` al final del caso de uso.
- [ ] Ownership: filtrar por `user_id` cuando el recurso pertenece a un usuario.

## 5. Providers — `app/modules/<modulo>/providers/<modulo>_provider.py`

- [ ] `<Modulo>ServiceFactory(session)` con un método por servicio.

## 6. REST — `app/modules/<modulo>/rest/<recurso>/`

- [ ] `schemas.py` (Pydantic v2), `error_messages.py` (todos los códigos del servicio), `routes.py` (`APIRouter(prefix="/api/<recurso>")`).
- [ ] Auth: `token_required_actual` / `admin_required`.
- [ ] Registrar el router en `app/app_factory.py`.

## 7. Web (si el módulo tiene páginas)

- [ ] Seguir el checklist del skill `web-ui`: ruta en `web/routes.py`, prefijo en `_is_web_route()`, template, JS con `?v={{ sv }}`, enlace en el sidebar.

## 8. Verificar

- [ ] Arrancar el servidor (`uv run uvicorn app.main:app --reload`) y comprobar que importa sin errores.
- [ ] Probar los endpoints en Swagger (`/docs`) con la sesión del navegador. **No** hacer login con `curl`.
- [ ] Tests solo si el usuario los pide (skill `testing`).

## 9. Documentar

- [ ] Ejecutar el skill `update-specs`.
