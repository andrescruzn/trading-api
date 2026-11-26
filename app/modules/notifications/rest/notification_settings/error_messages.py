# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/rest/notification_settings/error_messages.py
#
# Textos de UI de la página Notificaciones y de los mensajes de prueba.
# ======================================================================

NOTIFICATION_SETTINGS_ERROR_MESSAGES: dict[str, str] = {
    "TELEGRAM_INVALID_UPDATES_MODE": "Elige cómo llegan las respuestas: apagado, consulta periódica o webhook.",
    "TELEGRAM_INVALID_CHAT_ID": "El chat por defecto debe ser un ID numérico (los grupos empiezan por -) o un @canal.",
    "TELEGRAM_TOKEN_REQUIRED": "Para activar Telegram, escribe el token del bot.",
    "TELEGRAM_TOKEN_INVALID": "Telegram no reconoció ese token. Cópialo de nuevo desde @BotFather.",
    "TELEGRAM_INVALID_WEBHOOK_URL": "La URL del webhook debe ser pública y empezar por https://.",
    "TELEGRAM_WEBHOOK_FAILED": "Telegram no aceptó la URL del webhook. Revisa que la API sea accesible desde internet. No se guardaron los cambios.",
    "TELEGRAM_NOT_ACTIVE": "Activa Telegram y guarda el token antes de enviar la prueba.",
    "TELEGRAM_NO_CHAT": "No hay a dónde enviar la prueba: conecta tu Telegram desde el menú de usuario o define un chat por defecto.",
    "TELEGRAM_SEND_FAILED": "Telegram no entregó el mensaje. Revisa que el bot pueda escribir en ese chat.",
    "EMAIL_NOT_CONFIGURED": "El servidor no tiene correo configurado (SMTP_HOST en el .env). Pídele a quien administra el servidor que lo configure.",
    "EMAIL_SEND_FAILED": "No pudimos enviar el correo de prueba. Revisa la configuración SMTP del servidor.",
    "USER_NOT_FOUND": "No encontramos tu cuenta. Vuelve a iniciar sesión.",
}

# Mensajes de prueba (rol notificación)
TELEGRAM_TEST_TEXT = "Trading App: la conexión con Telegram funciona. Aquí te llegarán los avisos."
EMAIL_TEST_SUBJECT = "Correo de prueba de Trading App"
EMAIL_TEST_TITLE = "La conexión de correo funciona"
EMAIL_TEST_MESSAGE = (
    "Este es un correo de prueba. Si lo recibes, los avisos por correo de "
    "Trading App llegarán a esta dirección."
)
