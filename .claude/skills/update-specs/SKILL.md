---
name: update-specs
description: Actualiza la documentación al cerrar un módulo o una feature significativa de Trading App — la spec specs/MNN-*.md, la tabla de estado de specs/_ROOT.md y la sección correspondiente de MANUAL.md. Usar al terminar un módulo, una feature, un fix relevante o al cerrar la sesión de trabajo, o cuando el usuario pida "actualiza la documentación/specs".
argument-hint: "[módulo, p. ej. M07]"
---

# Actualizar specs y manual

Módulo: **$ARGUMENTS** (si no se indica, el módulo en el que se trabajó en esta sesión).

Primero revisar qué cambió de verdad (`git diff develop...HEAD --stat` y los archivos tocados); documentar solo lo que está en el código, no lo planeado.

## 1. Spec del módulo — `specs/MNN-*.md`

Mantener el orden de secciones de la plantilla (ver `specs/_ROOT.md` → "Plantilla de spec") y actualizar solo lo que cambió:

| Sección | Qué tocar |
|---|---|
| Título | `✅ COMPLETO` / `📌 PENDIENTE` |
| **Ficha** | Estado, avance (entregables hechos / planificados), madurez, tablas, prefijo API, **Última revisión = fecha de hoy** |
| **Páginas** | Páginas nuevas, separando usuario y admin |
| **Entregables** | Marcar ✅ lo terminado; añadir los nuevos |
| **Decisiones de diseño** | Decisión · motivo · alternativa descartada |
| **Avance** | Recalcular alcance y madurez con la rúbrica de `_ROOT.md`, anotando la evidencia |
| **Posibles mejoras** / **Fuera de alcance** | Quitar lo resuelto, añadir lo detectado (con prioridad y esfuerzo) |
| **Detalle técnico** | Tablas, modelos, repos, servicios, endpoints, páginas, settings nuevos |
| **Gotchas críticos** | Todo bug o trampa descubierta en la sesión (síntoma → causa → solución) |
| **Tests** | Archivos de test existentes y qué cubren |
| **Historial** | Una línea con fecha y resumen del cambio |

## 2. Índice — `specs/_ROOT.md`

- [ ] Fila del módulo en "Estado del proyecto": estado, alcance %, madurez %, descripción. Recalcular la fila **Promedio**.
- [ ] "Mapa de páginas" (rutas del frontend React) si hay pantallas nuevas.
- [ ] "Estado real del flujo" si cambió qué está automatizado.
- [ ] "Prioridades transversales" si se resolvió o apareció una prioridad.

## 3. Manual — `MANUAL.md`

- [ ] Sección del módulo en lenguaje simple, sin tecnicismos: qué hace, para qué sirve, cómo se usa desde la web (pasos), y un ejemplo con números si aplica a trading.
- [ ] Si se introdujo un concepto nuevo de trading (indicador, tipo de orden, métrica), explicarlo en la Parte 1.

## 4. Otros archivos (solo si aplica)

- [ ] `CLAUDE.md`: solo si cambió una regla global, un comando o se añadió un skill. No meter detalle de módulo.
- [ ] Skills: si se descubrió una convención o gotcha que aplica a todo el repo, añadirlo al skill correspondiente.
- [ ] Si hubo revisión de Alembic: confirmar que el usuario la aplicó (`alembic upgrade head`) y que `alembic check` sale limpio.

## 5. Cierre

Resumir al usuario qué se actualizó en cada archivo. Si algo quedó pendiente, decirlo explícitamente antes de cerrar.
