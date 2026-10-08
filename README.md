# Trading App

Aplicación **Trading App** (nombre temporal; el repo contiene la aplicación completa), construida con **FastAPI** sobre **Python 3.12**, orientada a trading algorítmico, IA y backtesting, y usa **MySQL 8.x** como base de datos principal.

El repo tiene dos partes que corren por separado:

- **API REST headless** (`app/`): FastAPI, todas las rutas bajo `/api` (Swagger en `/docs`). No sirve páginas.
- **Frontend** (`frontend/`): React + Vite + shadcn. Consume la API con la cookie de sesión.

---

## Entorno

Crear el entorno virtual con [uv](https://docs.astral.sh/uv/):

```bash
uv venv --python 3.12
```

Activar el entorno virtual:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (Git Bash)
source .venv/Scripts/activate
```

---

## Instalación

Instalar dependencias (`pyproject.toml` + `uv.lock`):

```bash
uv sync
```

Agregar / actualizar dependencias:

```bash
uv add <paquete>
uv add --dev <paquete>
uv lock --upgrade-package <paquete>
```

---

## Frontend

Requiere **Node.js 20.12+** (recomendado 22 o 24). Las configs (`package.json`, `vite.config.ts`, `tsconfig*.json`, `components.json`) están en la raíz del repo y el código en `frontend/`.

```bash
npm install                                 # dependencias
cp .env_frontend.example .env_frontend      # variables del front (VITE_*)
```

| Variable (`.env_frontend`) | Para qué |
|---|---|
| `VITE_API_URL` | Base de la API. En desarrollo `/api` (pasa por el proxy de Vite). En producción, la URL pública, idealmente en el mismo dominio que el front |
| `VITE_API_PROXY_TARGET` | Solo desarrollo: a dónde reenvía Vite las peticiones `/api` (por defecto `http://localhost:8000`) |

El front **no** lee el `.env` del backend: solo `.env_frontend`.

---

## Base de datos y migraciones

El esquema se gestiona con **Alembic** (`alembic.ini` + carpeta `database/migrations/`). La conexión se toma del `.env` (`DB_*`).

El esquema completo sale de los modelos ORM: las migraciones de `database/migrations/versions/` crean todas las tablas.

BD nueva desde cero:

```bash
uv run alembic upgrade head    # crea todas las tablas
```

Después, cargar los datos iniciales (roles, exchanges, timeframes, símbolos, estrategias de ejemplo):

```bash
uv run python -m database.seeds                      # todos (se pueden correr varias veces)
uv run python -m database.seeds roles market_data    # solo los indicados
uv run python -m database.seeds --list               # ver los disponibles
```

El seed `accounts` crea cuentas paper de ejemplo para el usuario demo; si ese usuario todavía no existe, se omite. Regístralo desde la web y vuelve a correr `uv run python -m database.seeds accounts`.

BD que ya tenía el esquema antes de Alembic (creada con el dump; solo una vez, no ejecuta SQL):

```bash
uv run alembic stamp head
```

### Crear y aplicar una migración

1. Crear o modificar el modelo ORM en `app/modules/<modulo>/infrastructure/` (si es nuevo, registrarlo en `app/extensions/db/models_registry.py`).

2. Generar la migración comparando los modelos con la BD:

   ```bash
   uv run alembic revision --autogenerate -m "m11 crear tabla x"
   ```

   Crea un archivo en `database/migrations/versions/` con `upgrade()` y `downgrade()`.

3. **Revisar el archivo generado antes de aplicarlo:**
   - En tablas nuevas incluye CHECKs, comentarios y defaults del modelo. En tablas existentes **no** detecta CHECKs añadidos o quitados ni cambios de `server_default`: añadirlos a mano, p. ej. con `op.create_check_constraint(...)`.
   - Borrar las operaciones que no deban ejecutarse.
   - Completar el `MOTIVO:` del docstring.

4. Aplicarla:

   ```bash
   uv run alembic upgrade head
   ```

### Otros comandos

```bash
uv run alembic upgrade head --sql     # ver el SQL sin ejecutarlo
uv run alembic current                # en qué revisión está la BD
uv run alembic history --verbose      # lista de revisiones
uv run alembic downgrade -1           # deshacer la última
uv run alembic check                  # ¿los modelos coinciden con la BD? (no escribe)
```

> **Importante:** si `alembic check` muestra diferencias que no vienen de tu cambio, la migración generada las incluirá todas (borrado de índices, cambios de tipo…) sobre tablas que ya funcionan. Antes de generar, alinea los modelos con la BD real: la BD es la fuente de verdad.

---

## Ejecución

Con el entorno activado:

```bash
uvicorn app.main:app --reload
```

O sin activarlo, usando uv:

```bash
uv run uvicorn app.main:app --reload
```

La API queda en `http://localhost:8000` (Swagger en `/docs`, rutas en `/api/*`, salud en `/health`).

En otra terminal, el frontend:

```bash
npm run dev            # http://localhost:5193  → abre http://localhost:5193/#/login
```

Otros comandos del front:

```bash
npm run check-types    # genera el árbol de rutas y revisa tipos
npm run build          # build de producción en frontend/dist
npm run preview        # sirve el build localmente
```

### Producción

- Sirve `frontend/dist` como sitio estático (usa hash routing: `/#/bots`, no necesita reescrituras).
- Publica la API en el **mismo dominio** detrás de un reverse proxy en `/api` (así la cookie `SameSite=Lax` funciona) y define `CORS_ORIGINS` con el origen del front.
- Si el front y la API viven en dominios distintos: `AUTH_COOKIE_SAMESITE=None`, HTTPS obligatorio y `VITE_API_URL` con la URL completa de la API.
