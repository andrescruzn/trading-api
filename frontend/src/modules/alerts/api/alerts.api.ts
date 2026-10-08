import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// ======================================================================

type AlertRuleType = 'signal' | 'price' | 'pnl' | 'drawdown' | 'error';
type AlertSeverity = 'info' | 'warning' | 'critical';
type AlertDeliveryStatus = 'pending' | 'sent' | 'failed';
type SignalActionFilter = 'any' | 'buy' | 'sell' | 'hold';
type PriceOperator = 'lt' | 'lte' | 'gt' | 'gte';
type PnlPeriod = 'daily' | 'total';

/**
 * JSON libre del backend; los campos dependen del tipo de regla:
 * - signal: `{action}` · price: `{symbol_id, operator, threshold}`
 * - pnl: `{threshold, period}` · drawdown: `{threshold}` · error: `{}`
 */
type AlertRuleSpec = {
	action?: SignalActionFilter;
	symbol_id?: number;
	operator?: PriceOperator;
	threshold?: number;
	period?: PnlPeriod;
};

/** `webhook` es la URL o `false` si no se usa. */
type AlertChannels = {
	email?: boolean;
	telegram?: boolean;
	desktop?: boolean;
	webhook?: string | false;
};

type AlertRule = {
	id: number;
	name: string;
	rule_type: AlertRuleType;
	rule_spec: AlertRuleSpec;
	channels: AlertChannels;
	is_active: boolean;
	user_id: number | null;
	/** `null` = aplica a cualquier bot del usuario. */
	bot_id: number | null;
	created_at: string | null;
};

type AlertEvent = {
	id: number;
	alert_rule_id: number | null;
	user_id: number | null;
	bot_id: number | null;
	ts: string | null;
	severity: AlertSeverity;
	title: string;
	message: string | null;
	payload: Record<string, unknown>;
	delivery_status: AlertDeliveryStatus;
};

type AlertRuleInput = {
	name: string;
	rule_type: AlertRuleType;
	rule_spec: AlertRuleSpec;
	channels: AlertChannels;
	bot_id: number | null;
};

/** El backend no permite cambiar el tipo ni el bot de una regla existente. */
type AlertRuleUpdate = {
	name?: string;
	rule_spec?: AlertRuleSpec;
	channels?: AlertChannels;
	is_active?: boolean;
};

type AlertEventFilters = {
	limit?: number;
	from_ts?: string;
};

type TelegramTestResult = { ok: boolean };

// ======================================================================
// Reglas de alerta
// ======================================================================

/** Usuario: sus reglas. Admin: todas (incluye `user_id`). */
function listAlertRules() {
	return api.get<AlertRule[]>('/alert-rules');
}

function createAlertRule(input: AlertRuleInput) {
	return api.post<AlertRule>('/alert-rules', input);
}

function updateAlertRule(id: number, input: AlertRuleUpdate) {
	return api.put<AlertRule>(`/alert-rules/${id}`, input);
}

// ======================================================================
// Eventos de alerta
// ======================================================================

/** Usuario: sus eventos. Admin: todos. Del más reciente al más antiguo. */
function listAlertEvents(filters: AlertEventFilters = {}) {
	return api.get<AlertEvent[]>('/alert-events', filters);
}

// ======================================================================
// Telegram (solo admin)
// ======================================================================

/** Envía un mensaje de prueba al chat configurado en el servidor. */
function sendTelegramTest() {
	return api.post<TelegramTestResult>('/alerts/test-telegram');
}

export type {
	AlertChannels,
	AlertDeliveryStatus,
	AlertEvent,
	AlertEventFilters,
	AlertRule,
	AlertRuleInput,
	AlertRuleSpec,
	AlertRuleType,
	AlertRuleUpdate,
	AlertSeverity,
	PnlPeriod,
	PriceOperator,
	SignalActionFilter,
	TelegramTestResult,
};
export {
	createAlertRule,
	listAlertEvents,
	listAlertRules,
	sendTelegramTest,
	updateAlertRule,
};
