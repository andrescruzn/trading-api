---
name: web-ui
description: Páginas web server-side de Trading AI API (Jinja2 + JS vanilla + app.css). Usar antes de crear o modificar una página, template, archivo JS de /static/, estilos CSS o la navegación lateral. Cubre registro de la página en web/routes.py, prefijos de CSP en security_headers.py, cache-busting ?v={{ sv }}, handlers sin inline, escape de HTML, consumo del envelope de la API y componentes CSS existentes.
---

# Web UI (Jinja2 + JS vanilla)

La UI no es una SPA: FastAPI sirve HTML con Jinja2 y cada página carga su propio JS, que consume la API REST con `fetch` (la cookie HTTP-only viaja sola).

## Dónde vive cada cosa

| Pieza | Ruta |
|---|---|
| Ruta de la página | `app/modules/web/routes.py` (`web_router`) |
| Layout | `app/templates/base.html` (head, fuentes, Lucide) → `base_app.html` (sidebar + topbar) |
| Template | `app/templates/<modulo>/index.html` · admin: `app/templates/admin/<recurso>.html` |
| JS | `app/static/js/<modulo>/index.js` · admin: `app/static/js/admin/<recurso>.js` |
| CSS | `app/static/css/app.css` (único archivo, variables CSS como `--gold`, `--text-muted`) |
| CSP | `app/common/security/security_headers.py` → `_is_web_route()` |
| Mapa de páginas | `specs/_ROOT.md` → "Mapa de páginas web" |

## Checklist de página nueva

1. **Ruta** en `web/routes.py`, con el mismo patrón que las existentes:
   ```python
   @web_router.get("/admin/<recurso>", response_class=HTMLResponse, include_in_schema=False)
   def admin_recurso_page(request: Request):
       identity = _get_identity_from_cookie(request)
       if not identity:
           return RedirectResponse(url="/login", status_code=302)
       if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
           return RedirectResponse(url="/dashboard", status_code=302)
       return templates.TemplateResponse(request, "admin/<recurso>.html")
   ```
   `TemplateResponse(request, "template.html", {contexto})`: el `request` va **primero** (formato nuevo de Starlette).
2. **Prefijo CSP:** si la URL empieza con un prefijo nuevo, añadirlo a `web_prefixes` en `_is_web_route()`. Si no, la página recibe la CSP de la API y se rompe.
3. **Template** que extiende `base_app.html` con los bloques `title`, `nav_title`, `content` y `page_scripts`.
4. **Script con cache-busting:**
   ```html
   {% block page_scripts %}
     <script src="/static/js/<modulo>/index.js?v={{ sv }}"></script>
   {% endblock %}
   ```
   `sv` es un global de Jinja que cambia en cada reinicio del servidor. **Sin `?v={{ sv }}` el navegador sirve el JS viejo.** Aplica también a CSS.
5. **Enlace en el sidebar** de `base_app.html` (`sidebar__link` con `data-path`), en la sección de usuario o admin.
6. **Actualizar** el mapa de páginas de `specs/_ROOT.md` y la sección "Páginas" de la spec del módulo.

## Reglas de JS

- `'use strict';` y cabecera con la página que controla.
- **Nada de handlers inline** (`onclick`, `onchange`, `onsubmit`…) en HTML ni en strings generados por JS. Usar `addEventListener`, y para filas dinámicas delegación de eventos con `data-*`:
  ```js
  tbody.addEventListener('click', e => {
    const btn = e.target.closest('[data-action="detail"]');
    if (btn) openDetail(Number(btn.dataset.id));
  });
  ```
- Inicializar en `document.addEventListener('DOMContentLoaded', ...)`.
- **Escapar** todo dato del servidor antes de meterlo en `innerHTML` (helper `esc()` local) o usar `textContent`.
- Consumir el envelope: `const json = await res.json(); if (json.errorCode >= 400) showAlert(json.msg);` y los datos en `json.data` (en listados `json.data` **es** el array).
- Mostrar mensajes con el contenedor `#alert-msg` (`alert alert--error|success|info`), no con `alert()`.
- Iconos: Lucide (`<i data-lucide="nombre">`), y llamar `lucide.createIcons()` tras renderizar contenido dinámico.

## CSS

- Reutilizar los componentes de `app.css` antes de crear estilos: `.card`, `.btn` (`--primary`, `--secondary`, `--ghost`, `--danger`, `--sm`), `.alert`, `.data-table`, `.page-header`, `.divider`, `.spinner`, `.hidden`, `.text-muted`.
- Colores con las variables CSS del tema, no hex sueltos.
- Estilos nuevos en `app.css`; evitar `style="..."` inline en código nuevo.

## Deuda conocida (no replicar)

- La CSP web aún permite `'unsafe-inline'` en `script-src` y `style-src`. El objetivo es quitarlo, por eso las reglas de arriba.
- Quedan `onclick` inline en `admin/billing`, `admin/investors`, `admin/managed_accounts` y `bots/index` (templates y JS). Si se tocan esas páginas, migrarlos a `addEventListener`.
