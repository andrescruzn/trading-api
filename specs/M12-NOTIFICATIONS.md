# Módulo 12 — Notificaciones ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 7/7 entregables |
| Madurez (estimada) | 64 % — ver [Avance](#avance) |
| Tablas | `notification_settings` (R/W, una fila); `users` (R: `telegram_chat_id`, `email` de quien prueba) |
| Depende de | Solo `app/common` (cifrado, guarda de URLs); mailer para el correo de prueba |
| Lo usan | [M9](M09-ALERTS.md) (alertas, señal por aprobar, señales compartidas, avisos del fondo, bot de Telegram), [M1](M01-AUTH.md) (vínculo del chat y `GET /users/me`), [M7](M07-BOTS-SIGNALS.md) (seguir agentes compartidos), scheduler (polling de Telegram) |
| Prefijo API | `/api/notification-settings` |
| Frontend | `frontend/src/modules/notifications` |
| Última revisión | 2026-11-26 |

## Descripción

**En palabras simples:** Es el panel donde el super admin decide **por dónde llegan los avisos** de Trading App: Telegram y correo. Antes Telegram se configuraba en el archivo `.env` del servidor y había que reiniciar la API; ahora se escribe en la app y aplica al momento.

**Qué hace:**
- **Telegram:** interruptor, token del bot (se guarda cifrado y nunca se muestra), @usuario del bot (lo detecta solo al guardar el token), chat por defecto y cómo llegan las respuestas del bot (solo enviar · consulta periódica · webhook). En modo webhook el servidor genera la clave secreta y registra la URL en Telegram.
- **Correo:** interruptor de los avisos por correo. El servidor SMTP sigue en el `.env`; si falta, la página lo dice.
- **Prueba de cada canal:** mensaje de Telegram al chat de quien prueba (o al chat por defecto) y correo a su propia dirección.
- Con el correo encendido, llegan por correo **los mismos avisos que por Telegram**: señales por aprobar (con botón a la app; desde el correo no se decide), señales de agentes que sigues, alertas y avisos del fondo. El código de acceso y las invitaciones salen siempre.

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Administrador (super admin edita; el socio ve en solo lectura):**
- `/#/admin/notifications` — "Notificaciones" (Administración, ítem propio): tarjetas **Telegram** y **Correo** con su estado (Activo / Apagado / Sin configurar), guardar y enviar prueba. `/#/admin/telegram` redirige aquí.

## Entregables

- ✅ Tabla `notification_settings` (una fila, CHECK de modo) + modelo registrado en `models_registry.py`
- ✅ Dominio: `NotificationSettings`, `NotificationSettingsReader` / `NotificationSettingsRepository`, `TelegramGateway`
- ✅ Infraestructura: repositorio con cifrado Fernet; `telegram_api` (movido desde `alerts/channels/telegram_channel.py`, que lo reexporta) + `HttpTelegramGateway`
- ✅ Servicios: leer, guardar Telegram (valida con `getMe`, registra/borra el webhook), guardar correo, probar Telegram y correo
- ✅ REST `/api/notification-settings` (GET staff; PUT y POST super admin)
- ✅ Consumidores leen la BD en vez de `settings.TELEGRAM_*` (variables quitadas de `settings.py` y `.env.example`); correo de señal por aprobar y de señales compartidas (`NOTICE_TEMPLATE`)
- ✅ Front: página, ítem del menú, redirección de `/admin/telegram`; `GET /users/me` informa `telegram_available` y `email_notifications`

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| Módulo propio `notifications` que solo depende de `common` | `alerts`, `users`, `bots` y el scheduler lo leen; dentro de `alerts`, `users → alerts → users` haría ciclo | Guardar la configuración en el módulo alerts |
| Una sola fila (`id = 1` con CHECK), como `fund_settings` | Es configuración global; sin fila se usan los valores por defecto | Tabla clave-valor |
| Todas las variables de Telegram a la BD, **sin respaldo en `.env`** | Una sola fuente de verdad; con la BD vacía Telegram queda inactivo | Leer el `.env` si la BD está vacía |
| Token y secreto del webhook cifrados con `CredentialsCipher.encrypt_dict` (misma clave que las credenciales de exchange); un valor que no se puede descifrar se trata como vacío | Son credenciales; una clave rotada mal no debe tumbar los flujos de trading | Guardarlos en claro |
| La API nunca devuelve el token ni el secreto: `token_set`, `token_hint` (últimos 4) y `webhook_secret_set`; `bot_token` y `webhook_secret` redactados en la auditoría | Ni el socio ni un log pueden leerlos | Mostrar el token enmascarado desde el servidor |
| Token vacío al guardar = conservar el guardado | El formulario no puede rellenarse con el token | Exigirlo en cada guardado |
| Token nuevo → `getMe`: valida y toma el @usuario del bot | Error temprano y un campo menos | Pedir el @usuario a mano |
| Webhook: el admin escribe la URL pública (el front propone `VITE_API_URL` + `/telegram/webhook`), el servidor genera el secreto y llama `setWebhook`; si Telegram falla no se guarda nada | El secreto ya no está en el `.env`: el `curl` manual dejó de ser viable | Registrar el webhook a mano |
| Al pasar a polling (o salir de webhook) se llama `deleteWebhook` (best effort) | `getUpdates` no funciona con un webhook registrado | Dejarlo al admin |
| Lectura por sesión (`session.get` de la fila; el identity map evita repetir la query en un request), sin caché global | API y scheduler son procesos distintos: un caché en memoria quedaría viejo | Caché con TTL |
| Canal apagado = no se intenta (no cuenta como entrega `failed` en `alert_events`) | Apagar un canal es una decisión, no un fallo | Marcar fallido |
| El correo de prueba se envía en el momento (no en segundo plano) y funciona con el canal apagado | Hay que informar si llegó y poder probar antes de encender | Encolarlo |
| `email_enabled` por defecto **encendido** | Antes el correo salía siempre que hubiera SMTP: no cambia el comportamiento al migrar | Apagado por defecto |
| Seguir un agente compartido exige un canal: correo activo (todos tienen correo) o Telegram activo y vinculado; sin ninguno activo → `SUBSCRIPTION_NO_CHANNEL` 503 | Antes Telegram era el único canal | Seguir exigiendo Telegram |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (7/7) | Tabla, dominio, infraestructura, servicios, REST, consumidores y front |
| Madurez | **≈ 64 %** | Funcionalidad 85 · Tests 5 · Seguridad 85 · Operación 80 |

- **Funcionalidad (85):** configuración en caliente de Telegram y correo, prueba de cada canal, webhook registrado por el servidor; los avisos de señales salen también por correo. Falta: ver el estado del webhook en Telegram (`getWebhookInfo`) y quitar el token guardado.
- **Tests (5):** sin tests propios de los servicios del módulo; los tests de los consumidores (`tests/alerts/test_fire_alert_routing.py`, `tests/bots/test_shared_signal_notifier.py`, `tests/bots/test_signal_subscription_services.py`, `tests/scheduler/test_execution_cycle.py`) se adaptaron a la configuración en BD.
- **Seguridad (85):** token y secreto cifrados y fuera de las respuestas y de la auditoría; escrituras solo super admin; URL del webhook con la guarda SSRF; secreto comparado en tiempo constante.
- **Operación (80):** migración Alembic, sin reinicios para cambiar canales; el scheduler lee el modo de respuestas en cada ciclo.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Media | Tests de `UpdateTelegramSettingsService` (token, chat, webhook, borrado del webhook) y de las pruebas de canal | S |
| Media | Estado del webhook en la página (`getWebhookInfo`: último error, updates pendientes) | S |
| Baja | Botón para quitar el token guardado | S |
| Baja | Preferencias por persona (elegir correo y/o Telegram) | M |
| Baja | Mover también el SMTP a la BD | M |

## Fuera de alcance y pendientes conocidos

- El SMTP sigue en el `.env` (lo usa también el código de acceso).
- Preferencias de canal por usuario: hoy el interruptor es global.

## Detalle técnico

### Tabla `notification_settings`

| Columna | Tipo | Nota |
|---|---|---|
| `id` | BIGINT | Siempre 1 (`chk_notification_settings_single_row`) |
| `telegram_enabled` | BOOL, default 0 | Interruptor |
| `telegram_bot_token_enc` | TEXT NULL | Fernet `{"value": token}` |
| `telegram_bot_username` | VARCHAR(64) | De `getMe` |
| `telegram_default_chat_id` | VARCHAR(64) | ID numérico (grupos con `-`) o `@canal` |
| `telegram_updates_mode` | VARCHAR(16), default `off` | `off` \| `polling` \| `webhook` (`chk_notification_settings_updates_mode`) |
| `telegram_webhook_url` | VARCHAR(2048) | URL https registrada |
| `telegram_webhook_secret_enc` | TEXT NULL | Fernet |
| `email_enabled` | BOOL, default 1 | Interruptor del correo |
| `updated_by_user_id` | BIGINT FK users (SET NULL) | |
| `created_at` / `updated_at` | TIMESTAMP(6) | |

### Código (`app/modules/notifications/`)

| Capa | Archivo | Contenido |
|---|---|---|
| domain | `notification_settings_entity.py` | `NotificationSettings` (`telegram_active`, `telegram_token` — `""` si está apagado —, `email_active`, `token_hint()`, `receives_updates(mode)`), `UPDATES_MODES` |
| domain | `notification_settings_repository.py` | `NotificationSettingsReader` (`get()`), `NotificationSettingsRepository` (+ `save()`) |
| domain | `telegram_gateway.py` | `TelegramGateway` (`get_me`, `set_webhook`, `delete_webhook`, `send_message`) |
| infrastructure | `notification_settings_model.py` / `notification_settings_repository_impl.py` | Modelo + `SqlAlchemyNotificationSettingsRepository` (cifra/descifra) |
| infrastructure | `telegram_api.py` | `telegram_api(token, method, payload)` (token nunca en logs) + `HttpTelegramGateway` |
| services/settings | `get_notification_settings_service.py`, `update_telegram_settings_service.py`, `update_email_settings_service.py`, `send_test_services.py` | Casos de uso |
| providers | `notification_provider.py` | `NotificationServiceFactory(session)`, `build_notification_settings_reader(session)`, `build_notification_mailer()` |
| rest | `notification_settings/` | `routes.py`, `schemas.py`, `error_messages.py` (incluye los textos de las pruebas) |

Códigos de error: `TELEGRAM_INVALID_UPDATES_MODE`, `TELEGRAM_INVALID_CHAT_ID`, `TELEGRAM_TOKEN_REQUIRED`, `TELEGRAM_TOKEN_INVALID` (422) · `TELEGRAM_INVALID_WEBHOOK_URL` (422) · `TELEGRAM_WEBHOOK_FAILED` (502) · `TELEGRAM_NOT_ACTIVE` (409) · `TELEGRAM_NO_CHAT` (422) · `TELEGRAM_SEND_FAILED` (502) · `EMAIL_NOT_CONFIGURED` (503) · `EMAIL_SEND_FAILED` (502) · `USER_NOT_FOUND` (404).

### Endpoints REST

| Método | Ruta | Auth | Nota |
|---|---|---|---|
| GET | `/api/notification-settings` | staff | `{telegram: {enabled, active, token_set, token_hint, bot_username, default_chat_id, updates_mode, webhook_url, webhook_secret_set}, email: {enabled, smtp_configured}, updated_at}` |
| PUT | `/api/notification-settings/telegram` | super admin | `{enabled, bot_token?, default_chat_id?, updates_mode, webhook_url?}` → configuración completa |
| PUT | `/api/notification-settings/email` | super admin | `{enabled}` |
| POST | `/api/notification-settings/telegram/test` | super admin | Al chat de quien prueba, si no al chat por defecto → `{target: own_chat \| default_chat}` |
| POST | `/api/notification-settings/email/test` | super admin | Al correo de quien prueba → `{to_email}` |

Reemplaza a `POST /api/alerts/test-telegram` (retirado).

### Quién lee la configuración

| Consumidor | Qué usa |
|---|---|
| `FireAlertService` ([M9](M09-ALERTS.md)) | Telegram activo y chat por defecto; correo activo |
| `SignalApprovalNotifier` / `SharedSignalNotifier` ([M9](M09-ALERTS.md)) | Token; correo activo + mailer (`NOTICE_TEMPLATE`, textos en `alerts/channels/signal_email_messages.py`) |
| `FundNoticeService` ([M9](M09-ALERTS.md)/[M11](M11-FUND.md)) | Token; correo activo |
| `build_telegram_update_service`, `POST /api/telegram/webhook` | Token, modo `webhook` y secreto |
| `execution_cycle._poll_telegram` | `_telegram_polling_token()` (sesión propia): token solo en modo `polling` |
| `TelegramLinkService` ([M1](M01-AUTH.md)) | Telegram activo + @usuario (`TELEGRAM_NOT_CONFIGURED` si falta) |
| `GetMeService` ([M1](M01-AUTH.md)) | `telegram_available`, `email_notifications` |
| `SubscribeToBotService` ([M7](M07-BOTS-SIGNALS.md)) | Correo activo (+ SMTP) o Telegram activo |

### Frontend (`frontend/src/modules/notifications/`)

| Ruta | Archivo de ruta | Página / componentes |
|---|---|---|
| `/#/admin/notifications` | `routes/_app/admin/notifications.lazy.tsx` | `pages/admin-notifications.tsx` + `components/telegram-settings-card.tsx`, `email-settings-card.tsx`, `channel-status-badge.tsx` |
| `/#/admin/telegram` | `routes/_app/admin/telegram.tsx` | Redirige a `/admin/notifications` |

- API `api/notification-settings.api.ts`; hooks `use-notification-settings-queries.ts` / `-mutations.ts` (los PUT guardan la respuesta con `setQueryData`); etiquetas `lib/notifications-labels.ts` (`suggestedWebhookUrl()`).
- Sidebar: Administración → **Notificaciones** (`IconBellCog`), visible para super admin y socio.

## Gotchas críticos

- **Clave Fernet:** el token se cifra con `CREDENTIALS_SECRET_KEY`. Si se cambia sin pasar la vieja a `CREDENTIALS_PREVIOUS_KEYS`, el token no se puede descifrar: Telegram queda inactivo (log `notification_settings: no se pudo descifrar el token`) y hay que volver a escribirlo.
- **Polling y webhook a la vez:** `getUpdates` falla con un webhook registrado. Guardar el modo `polling` en la página borra el webhook; si se registró a mano, también.
- **Token nuevo = secreto nuevo:** al cambiar de bot en modo webhook se genera otro secreto y se vuelve a registrar.
- **Sin SMTP en el `.env`** el interruptor del correo no basta: no sale ningún correo (la página muestra el aviso y `GET /users/me` devuelve `email_notifications: false`).

## Tests

- Sin tests propios del módulo. Los consumidores adaptados: `tests/alerts/test_fire_alert_routing.py`, `tests/bots/test_shared_signal_notifier.py`, `tests/bots/test_signal_subscription_services.py`, `tests/scheduler/test_execution_cycle.py` (`TestPollTelegram`).

## Riesgos

- Quien sea super admin ve y cambia el bot: con otro token, los chats vinculados dejan de recibir (cada persona debe volver a conectar su Telegram con el bot nuevo).
- El chat por defecto recibe las alertas de quien no conectó Telegram: dejarlo vacío para no enviar nada sin vínculo.

## Historial

- **2026-11-26** — Módulo creado: Telegram sale del `.env` a la BD (`notification_settings`, cifrado), canal Email con interruptor y prueba, página `/#/admin/notifications` (ítem propio en Administración; Telegram sale de Configuración), correo para señales por aprobar y señales compartidas, `POST /api/alerts/test-telegram` retirado.
