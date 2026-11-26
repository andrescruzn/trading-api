import type { TelegramUpdatesMode } from '@/modules/notifications/api/notification-settings.api';
import type { SelectOption } from '@/modules/shared/components/option-select';

const UPDATES_MODE_LABELS: Record<TelegramUpdatesMode, string> = {
	off: 'Solo enviar avisos',
	polling: 'Consulta periódica (desarrollo)',
	webhook: 'Webhook (producción)',
};

const UPDATES_MODE_DESCRIPTIONS: Record<TelegramUpdatesMode, string> = {
	off: 'Los avisos salen, pero los botones Aprobar y Descartar y la vinculación de chats no responden.',
	polling:
		'El servidor pregunta a Telegram cada minuto. Úsalo cuando la API no tiene una URL pública.',
	webhook:
		'Telegram avisa al instante a la API. Necesita una URL pública con https.',
};

const UPDATES_MODE_OPTIONS: SelectOption[] = (
	Object.keys(UPDATES_MODE_LABELS) as TelegramUpdatesMode[]
).map((value) => ({ value, label: UPDATES_MODE_LABELS[value] }));

/** URL del webhook que se propone: la API que usa este front. */
function suggestedWebhookUrl(): string {
	const base = (
		import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'
	).replace(/\/+$/, '');
	return `${base}/telegram/webhook`;
}

export {
	suggestedWebhookUrl,
	UPDATES_MODE_DESCRIPTIONS,
	UPDATES_MODE_LABELS,
	UPDATES_MODE_OPTIONS,
};
