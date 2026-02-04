# Claude Instructions — Project Architecture & Code Standards (PYTHON)

Este proyecto es un **backend en Python** (FastAPI) y sigue estrictamente los siguientes lineamientos.
Claude debe comportarse como un **asistente técnico crítico y disciplinado**, no como un generador automático de código.

Estas reglas son **obligatorias** y tienen prioridad sobre cualquier sugerencia por defecto.

---

## 1. Principios SOLID y DRY

- El diseño del código debe minimizar la duplicación y maximizar la mantenibilidad.
- Evitar lógica repetida, responsabilidades mezcladas o implícitas.
- Cada componente debe tener un propósito claro y verificable.

---

## 2. Screaming Architecture

- La estructura del proyecto debe comunicar claramente su **propósito y dominio**.
- La arquitectura debe “gritar” **qué hace el sistema**, no qué tecnología utiliza.
- Evitar estructuras centradas en frameworks o detalles técnicos.

---

## 3. Modularidad y Principio de Responsabilidad Única (SRP)

- Cada módulo, clase o archivo debe tener **una única responsabilidad**.
- No se permiten módulos “catch-all” ni clases multi-propósito.

---

## 4. Uso de Patrones de Diseño

- Los patrones deben usarse **solo cuando aporten valor real**.
- Todo patrón aplicado debe:
  - Ser explícitamente mencionado.
  - Ser explicado (por qué se usa y qué problema resuelve).

Ejemplos esperados:

- Application Service
- Repository
- Factory
- Strategy
- Presenter / Serializer

---

## 5. Actitud Técnica y Crítica

- Claude debe proponer mejoras **sin filtro**, incluso si implican refactorizaciones.
- Las propuestas pueden ser aceptadas o rechazadas conscientemente.
- **Nunca aplicar cambios sin autorización explícita del usuario.**

---

## 6. Arquitectura alineada a principios personales del proyecto

- El código debe respetar:
  - SOLID
  - DRY
  - Modularidad
  - Single Responsibility
- Garantizar compatibilidad con herramientas de análisis estático.
- Evitar imports ambiguos, dependencias implícitas y warnings evitables.

---

## 7. Eliminación de código innecesario

- No se permite:
  - Código muerto
  - Código duplicado
  - Código sin propósito claro
  - Código que no aporte valor al dominio

Todo código debe justificar su existencia.

---

## 8. Reutilización centralizada de utilidades (utils)

- Toda lógica reutilizable (utils, helpers, funciones transversales) debe ubicarse en: app/common/utils/

Reglas estrictas:

- ❌ Prohibido definir utils, helpers o hooks dentro de services.
- ✅ Los services deben **limitarse exclusivamente a orquestar lógica de negocio**.

---

## 9. Uso obligatorio de `__init__.py` como API explícita

- Cada paquete debe exponer una API clara mediante `__init__.py` (barrel exports).
- `__init__.py`:
  - ❌ No contiene lógica de negocio
  - ✅ Solo re-exporta símbolos

Buenas prácticas:

- ✅ Preferir imports desde el paquete:
  - `from app.modules.users.services import UserService`
- ❌ Evitar rutas de import largas, frágiles o dependientes de archivos internos.

---

## 10. Prevención estricta de dependencias cíclicas

La arquitectura debe respetar una **dirección única de dependencias**:

- `rest` → depende de `services`
- `services` → depende de `domain` e `infrastructure` (vía contratos)
- `infrastructure` → implementa contratos y depende de `domain`
- `domain` → no depende de ninguna otra capa

Reglas adicionales:

- ✅ Usar contratos / interfaces (Repository Pattern).
- ✅ Preferir imports relativos solo si ayudan a romper ciclos.
- ❌ Nunca importar desde `rest` hacia capas internas.
- ❌ Nunca permitir dependencias circulares entre módulos.

---

## 11. Separación estricta de presentación / UI concerns

- Los services:
  - Retornan **datos crudos de dominio** (ints, decimals, ISO, etc.).
  - Pueden retornar campos derivados de dominio (ej. `remaining_kcal`, `progress_percent`).

Formato y presentación:

- Deben ir en:
  - `app/common/utils/` (si es transversal), o
  - Presenters / Serializers en la capa REST.

Prohibiciones:

- ❌ Prohibido formatear labels, strings de UI, “pretty print” o conversiones de presentación dentro de services.
- ❌ Prohibido definir helpers locales (funciones anidadas) en services,
  salvo closures estrictamente necesarias y justificadas.

---

## 12. Revisión contextual antes de crear código nuevo

Antes de crear código reutilizable (utils, helpers, services, presenters, validators, etc.),
Claude debe realizar una **revisión razonable de la estructura existente**, basada en convención y ubicación.

Alcance de la revisión (no exhaustiva):

- Utils / helpers transversales:
  - `app/common/utils/`
- Servicios de dominio:
  - `app/modules/<modulo>/services/`
- Presenters / Serializers:
  - `app/modules/<modulo>/rest/` o `presenters/`
- Repositorios / infraestructura:
  - `app/modules/<modulo>/infrastructure/`

❗ No se exige búsqueda global en todo el repositorio.

---

## 13. Código siempre documentado

Todo código entregado debe estar **completamente comentado**.

Reglas:

- ✅ Usar separadores por secciones:
  - `# ======================================================================`
- ✅ Comentar intención y **por qué**, no solo “qué hace”.
- ✅ Comentar decisiones de negocio, validaciones, queries y transformaciones.
- ✅ Comentar parámetros relevantes cuando aporte claridad.
- ✅ Mantener comentarios alineados al **dominio**, no a la tecnología.

Reglas adicionales:

- ❌ No entregar código crudo sin estructura ni explicación.
- ✅ Dividir bloques largos en pasos numerados (1, 2, 3…).
- ✅ Indicar explícitamente patrones aplicados (Repository, Presenter, Service Result, etc.).

---

## Regla Final (Crítica)

- ❌ Claude **NO** debe modificar ni borrar archivos sin explicar primero qué va a cambiar.
- ❌ Claude **NO** debe aplicar cambios sin confirmación explícita.
- ✅ Claude debe priorizar **análisis, propuesta y control** sobre velocidad.

## Carpetas y archivos a ignorar

Claude debe **ignorar completamente** las siguientes carpetas y archivos,
salvo que se indique explícitamente lo contrario:

- venv/
- .venv/
- node_modules/
- **pycache**/
- .git/
- .idea/
- .vscode/
- dist/
- build/
- coverage/
- htmlcov/
- .pytest_cache/
- migrations/
- alembic/
- logs/
- tmp/
- media/
- static/

Claude debe enfocarse **exclusivamente** en el código fuente del proyecto,
principalmente dentro de:

- app/
