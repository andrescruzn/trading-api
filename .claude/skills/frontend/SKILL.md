---
name: frontend
description: Cómo se construye el frontend React de Trading App (frontend/). Usar antes de crear o modificar cualquier página, ruta, componente, hook, llamada a la API o item del sidebar del front. Cubre la estructura por módulos, TanStack Router (hash history, rutas finas, guards de rol), TanStack Query (api → queries → mutations), el api-client y el envelope {msg, errorCode, data}, formularios con react-hook-form + zod, DataTable, diálogos, toasts, tokens de color, variables de entorno (.env.frontend) y el checklist de página nueva.
---

# Frontend (React + shadcn)

SPA en `frontend/` que consume la API REST headless (`/api/*`). FastAPI **no** renderiza vistas. La sesión es una cookie HttpOnly: el JS nunca ve el token.

Stack: React 19 · Vite 8 · TypeScript 6 · TanStack Router (file-based, **hash history**) · TanStack Query 5 · shadcn estilo `base-vega` sobre **Base UI** (no Radix) · Tailwind 4 · react-hook-form + zod 4 · iconos `@tabler/icons-react` · zustand solo para el aviso de sesión expirada.

Skills relacionados: `shadcn` (añadir/usar componentes), `tailwind-css-patterns`, `typescript-advanced-types`, `copy-ux-writer` (todo texto visible), `frontend-design` (pantallas nuevas con diseño propio). Para el contrato de la API: `api-standards`.

## Estructura

```
package.json · vite.config.ts · tsr.config.json · tsconfig*.json · components.json   ← raíz del repo
.env.frontend (.example)                                                              ← variables VITE_*
frontend/
  index.html · public/favicon.svg
  src/
    main.tsx · app.tsx (QueryClient, AuthProvider, Toaster) · router.ts (hash history)
    index.css                 tokens de color/tipografía (:root y .dark) — NO cambiar la paleta
    routeTree.gen.ts          generado por `tsr generate` — no editar
    routes/                   rutas de archivo, finas
      __root.tsx              MainLayout: carga /users/me antes de renderizar
      _auth.tsx · _auth/login.lazy.tsx
      _app.tsx                AppShellLayout (sidebar + breadcrumb); sin sesión → /login
      _app/<pagina>.lazy.tsx
      _app/admin.tsx          AdminGuardLayout (rol admin) → _app/admin/*.lazy.tsx
      _app/investor.tsx       InvestorGuardLayout (rol investor) → _app/investor/*.lazy.tsx
    modules/
      ui/                     primitivas shadcn (Base UI). Se añaden con el CLI de shadcn; no meter lógica de negocio
      shared/                 api-client, types/api.ts, lib/format.ts, DataTable, OptionSelect, StatCard,
                              ErrorAlert, PageListHeader, TablePagination, layouts, páginas de error
      app-shell/              sidebar (app-sidebar.tsx), nav-user, breadcrumb, layout autenticado
      auth/                   login (solo código OTP), AuthProvider/useAuth, roles, guards
      <dominio>/              market · features · accounts · strategies · agent · bots · orders · alerts · billing · dashboard
        api/<dominio>.api.ts          funciones + tipos del JSON del backend
        hooks/use-<dominio>-queries.ts    query keys + useQuery
        hooks/use-<dominio>-mutations.ts  useMutation + invalidación
        lib/<dominio>-labels.ts       etiquetas en español, opciones de selects, helpers puros
        components/                   diálogos, formularios, tablas propias del dominio
        pages/<pagina>.tsx            una página por ruta (`<Nombre>Page`)
```

Un módulo del front por módulo de backend (M2 → `market`, M3 → `features`, M4 → `accounts`, M5 → `strategies`, M6 → `agent`, M7 → `bots`, M8 → `orders`, M9 → `alerts`, M10 → `billing`). Un módulo puede importar `api`/`hooks`/`lib` de otro (p. ej. `bots` usa `useSymbolsQuery` de `market`); nunca sus `pages`.

## Rutas

- El archivo de ruta solo conecta la URL con la página:
  ```tsx
  // routes/_app/bots.lazy.tsx
  export const Route = createLazyFileRoute('/_app/bots')({ component: BotsPage });
  ```
- Search params tipados: archivo base `x.tsx` con `validateSearch` (zod con `.catch()` para no romper la ruta) + `x.lazy.tsx` con el componente. La página los lee con `getRouteApi('/_app/x').useSearch()`. Ejemplo: `routes/_app/market/candles.tsx`.
- **Hash history**: las URLs son `/#/bots`. Los `<Link to="/bots">` no llevan `#`.
- Páginas de admin bajo `_app/admin/`, de inversor bajo `_app/investor/`: el guard ya está en el layout. Igual el backend valida el rol en cada endpoint; el guard es solo UX.
- Tras crear/renombrar rutas, `pnpm check-types` regenera `routeTree.gen.ts`.

## Datos: api → queries → mutations

1. **`api/<x>.api.ts`**: tipos que reflejan el JSON **tal cual lo manda el backend (snake_case)**, sin capa de mapeo. Decimales (`DECIMAL(30,12)`) llegan como `string`: se formatean, no se convierten para guardar. Funciones finas sobre `api` del api-client:
   ```ts
   function listBots(filters: { account_id?: number } = {}) {
     return api.get<Bot[]>('/bots', filters);          // → GET /api/bots?account_id=…
   }
   function startBot(id: number) {
     return api.post<Bot>(`/bots/${id}/start`);
   }
   ```
   Las rutas se escriben **sin** `/api`: el prefijo lo pone `VITE_API_URL`.
2. **`hooks/use-<x>-queries.ts`**: query keys como constantes (`BOTS_QUERY_KEY = ['bots'] as const`), filtros dentro de la key, `enabled` cuando faltan parámetros, `placeholderData: keepPreviousData` en listas filtrables, `staleTime` largo en catálogos (símbolos, timeframes).
3. **`hooks/use-<x>-mutations.ts`**: `useMutation` + `queryClient.invalidateQueries` en `onSuccess` de todo lo que cambió. Los toasts van en la página/diálogo (callbacks de `mutate`), no en el hook.
4. **Nunca** `fetch` directo ni `useEffect` para cargar datos.

### api-client y errores

`modules/shared/lib/api-client.ts`:
- `credentials: 'include'` siempre (cookie HttpOnly). Sin headers de auth.
- Desempaqueta el envelope `{msg, errorCode, data}` y devuelve `data`. Si `errorCode >= 400` (o la respuesta no es JSON) lanza `ApiClientError(msg, status, data)`.
- `msg` ya es texto de UI en español (lo define el backend en `rest/<recurso>/error_messages.py`): se muestra tal cual con `getErrorMessage(error)`. Si un error sale como código crudo (`SOME_CODE`), el arreglo va en el `error_messages.py` del backend, no en el front.
- 422 de validación trae `data: [{field, message}]`.
- No hay refresh token: un 401 fuera del login cierra la sesión, muestra "Tu sesión expiró" y redirige a `/login`. Cada login rota el `jti`, así que iniciar sesión en otro navegador cierra la sesión actual.

## Auth y roles

- `useAuth()` → `{status, user, refreshUser, clear}`. `user` es `GET /users/me` (`role_code`, `role_label`, `full_name`, `email`…).
- Roles por **`role_code`** (`ROLES.USER | ADMIN | INVESTOR` en `auth/lib/roles.ts`), nunca por `role_id` ni `role_label`.
- Mostrar/ocultar UI: `<HasRole role={ROLES.ADMIN}>…</HasRole>` o `useHasRole(...)`.
- Login solo por código: `POST /users/login` con el correo envía el OTP → `POST /users/login/otp/verify` pone la cookie; después se llama `refreshUser()`. No hay contraseñas ni página de perfil.

## Páginas

Esqueleto de un listado (ver `modules/market/pages/admin-exchanges.tsx`):

```tsx
export function AdminExchangesPage() {
  usePageBreadcrumb([{ label: 'Administración' }, { label: 'Exchanges' }]);
  const exchangesQuery = useExchangesQuery();
  const [editing, setEditing] = useState<Exchange | null | undefined>(undefined); // undefined=cerrado, null=crear

  const columns: DataTableColumn<Exchange>[] = [ /* id, header, cell, className */ ];

  return (
    <div className="flex flex-col gap-6">
      <PageListHeader title="Exchanges" description="…"
        actions={[{ label: 'Nuevo exchange', icon: <IconPlus />, onClick: () => setEditing(null) }]} />
      <DataTable columns={columns} rows={exchangesQuery.data} getRowId={(r) => r.id}
        isLoading={exchangesQuery.isLoading} error={exchangesQuery.error}
        errorTitle="No pudimos cargar los exchanges" empty="Aún no hay exchanges. Crea el primero." />
      <ExchangeFormDialog open={editing !== undefined}
        onOpenChange={(open) => !open && setEditing(undefined)} exchange={editing ?? null} />
    </div>
  );
}
```

- **Breadcrumb**: `usePageBreadcrumb([...])` en cada página.
- **Encabezado**: `PageListHeader` (título, descripción, acciones que colapsan a menú "…" en móvil).
- **Tablas**: `DataTable` (skeleton, error inline, vacío, paginación en el navegador — hoy ningún endpoint pagina en servidor). Columna de acciones = una columna más; con varias acciones usa `DropdownMenu` con `IconDots`. Si la fila es clicable (`onRowClick`), las celdas con botones hacen `event.stopPropagation()`. Muestra nombres, no IDs crudos (cruza con las queries de catálogos).
- **Filtros**: `OptionSelect` con opción `'all'` y `aria-label`; el filtro va en la query key.
- **KPIs**: `StatCard`. Errores de carga fuera de tablas: `ErrorAlert`.
- **Formato**: `formatNumber`, `formatPrice`, `formatPercent` (ratio 0–1), `formatPercentValue` (ya en %), `formatDateTime`, `formatDate` de `shared/lib/format.ts` (locale `es-CO`). No `toFixed` sueltos en la UI.
- Etiquetas de enums del backend (`trend_up`, `paper`, `crypto_exchange`…) en `lib/<x>-labels.ts`, con su `*_OPTIONS` para selects.

## Formularios y diálogos

- react-hook-form + `zodResolver` + `Controller` + `Field` / `FieldLabel required` / `FieldError` / `FieldDescription` / `FieldGroup` (`ui/components/field.tsx`). Validaciones de cliente con los mismos límites que el schema Pydantic.
- Selects: `OptionSelect` (valor `string | null`) + `requiredSelectField('Elige…')`. Los IDs viajan como string en el form y se convierten con `Number()` al enviar.
- Números: `z.coerce.number()`; tipa el form como `useForm<z.input<typeof s>, unknown, z.output<typeof s>>`.
- Errores de servidor → toast (`toast.add({ title, description: getErrorMessage(error), type: 'error' })`); errores de campo → inline (solo cliente).
- Diálogo de formulario (ver `market/components/exchange-form-dialog.tsx`): `Dialog` → `DialogHeader` → `<form id="x-form" className="contents">` con `DialogBody` → `DialogFooter` con el submit `form="x-form"`. `form.reset(...)` en un `useEffect` al abrir. El mismo diálogo crea (`entity = null`) y edita.
- Confirmaciones destructivas o irreversibles (detener bot, cerrar período, desactivar): `AlertDialog` con estado `entity | null`.
- Detalle largo de solo lectura: `Sheet`.
- Éxito → `toast.add({ title: 'Bot creado', type: 'success' })` y cerrar el diálogo.

## Estilo y diseño

- **Colores**: solo tokens de `index.css` vía clases (`bg-primary`, `text-muted-foreground`, `text-destructive`, `bg-chart-1`…). Nada de hex sueltos ni de cambiar la paleta. Alza/baja: `text-chart-1` (verde) / `text-destructive` (rojo).
- Variantes de `Badge`/`Button`: `default`, `secondary`, `outline`, `destructive`, `ghost`.
- Responsive: grids `sm:grid-cols-2 lg:grid-cols-4`; tablas con scroll horizontal (ya lo hace `Table`).
- Texto: español, tuteo, directo (skill `copy-ux-writer`). Nunca nombres de otros proyectos.
- Código: kebab-case en archivos, tabs, comillas simples, named exports (`export function XPage`), en `api`/`hooks`/`lib` un `export { … }` agrupado al final. `cn` siempre desde `@/modules/ui/lib/utils`. Comentarios en español explicando el **porqué**.
- Archivos de contexto separados de su provider y su hook (`*-context.ts`, `*-provider.tsx`, `use-*.ts`) para no romper Fast Refresh.

## Variables de entorno

`.env.frontend` en la raíz (copiar de `.env.frontend.example`; no se commitea). `vite.config.ts` lo carga a mano: Vite **no** lee el `.env` del backend.

| Variable | Uso |
|---|---|
| `VITE_API_URL` | URL completa de la API; no hay proxy, se llama directo con CORS + `credentials: 'include'`. Dev: `http://localhost:8000/api` (siempre `localhost`, no `127.0.0.1`: mismo sitio que el front → cookie `SameSite=Lax` OK). Prod: URL pública de la API |

Solo las `VITE_*` llegan al navegador: nunca secretos. Nueva variable → `.env.frontend.example` + `frontend/src/vite-env.d.ts`.

## Comandos

```bash
pnpm install           # lo ejecuta el usuario
pnpm dev               # http://localhost:5193 (lo ejecuta el usuario; llama directo a la API en :8000)
pnpm check-types       # tsr generate + tsc -b — correr tras cada cambio
pnpm lint              # biome check (formato, imports, lint) — correr tras cada cambio
pnpm build             # build de producción en frontend/dist
pnpm dlx shadcn@latest add <componente>   # componentes nuevos → modules/ui/components (lo ejecuta el usuario)
```

## Checklist de página nueva

1. Endpoint existe en el backend (si no: skill `new-module` / `api-standards`).
2. Tipos + funciones en `modules/<x>/api/<x>.api.ts`.
3. Queries/mutations en `hooks/`.
4. Página en `pages/<pagina>.tsx` con `usePageBreadcrumb` + `PageListHeader`.
5. Ruta fina en `routes/_app/...` (o `_app/admin/...` / `_app/investor/...`).
6. Item en `navSections` de `modules/app-shell/components/app-sidebar.tsx` (con `role` si aplica).
7. `pnpm check-types` y `pnpm lint` sin errores.
8. Actualizar la spec del módulo (skill `update-specs`).

## Prohibido

- ❌ Renderizar HTML desde FastAPI o volver a Jinja2 para páginas.
- ❌ `fetch` directo, tokens en `localStorage`, headers `Authorization` desde el navegador.
- ❌ Traducir códigos de error en el front (va en `error_messages.py`).
- ❌ Decidir permisos por `role_id`/`role_label`.
- ❌ Editar `routeTree.gen.ts` o cambiar la paleta de `index.css`.
- ❌ Usar `npm`, `npx` o `pnpx`: solo `pnpm`, `pnpm exec <bin>` (binario del proyecto) o `pnpm dlx <paquete>` (sin instalar).
- ❌ Importar `cn` desde el paquete npm `cn` o librerías de UI fuera de shadcn/Base UI sin acordarlo.
