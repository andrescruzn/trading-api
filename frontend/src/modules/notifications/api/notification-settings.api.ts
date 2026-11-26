import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (JSON tal cual lo manda el backend)
// ======================================================================

/** off: no se procesan respuestas · polling: desarrollo · webhook: producción. */
type TelegramUpdatesMode = 'off' | 'polling' | 'webhook';

type TelegramSettings = {
	enabled: boolean;
	/** Encendido y con token: se puede enviar y recibir. */
	active: boolean;
	/** El token nunca viaja: solo si existe y sus últimos 4 caracteres. */
	token_set: boolean;
	token_hint: string | null;
	/** Lo detecta el servidor con el token (getMe). */
	bot_username: string | null;
	default_chat_id: string | null;
	updates_mode: TelegramUpdatesMode;
	webhook_url: string | null;
	webhook_secret_set: boolean;
};

type EmailSettings = {
	enabled: boolean;
	/** El servidor tiene SMTP en su .env (si no, no sale ningún correo). */
	smtp_configured: boolean;
};

type NotificationSettings = {
	telegram: TelegramSettings;
	email: EmailSettings;
	updated_at: string | null;
};

type TelegramSettingsInput = {
	enabled: boolean;
	/** Vacío = conservar el token guardado. */
	bot_token: string | null;
	default_chat_id: string | null;
	updates_mode: TelegramUpdatesMode;
	webhook_url: string | null;
};

type ChannelTestResult = { target?: string; to_email?: string };

// ======================================================================
// Funciones
// ======================================================================

function getNotificationSettings() {
	return api.get<NotificationSettings>('/notification-settings');
}

function updateTelegramSettings(input: TelegramSettingsInput) {
	return api.put<NotificationSettings>(
		'/notification-settings/telegram',
		input,
	);
}

function updateEmailSettings(enabled: boolean) {
	return api.put<NotificationSettings>('/notification-settings/email', {
		enabled,
	});
}

/** A tu chat vinculado o, si no tienes, al chat por defecto. */
function sendTelegramTest() {
	return api.post<ChannelTestResult>('/notification-settings/telegram/test');
}

/** A tu propio correo. */
function sendEmailTest() {
	return api.post<ChannelTestResult>('/notification-settings/email/test');
}

export type {
	ChannelTestResult,
	EmailSettings,
	NotificationSettings,
	TelegramSettings,
	TelegramSettingsInput,
	TelegramUpdatesMode,
};
export {
	getNotificationSettings,
	sendEmailTest,
	sendTelegramTest,
	updateEmailSettings,
	updateTelegramSettings,
};
