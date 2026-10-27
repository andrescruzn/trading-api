import { api } from '@/modules/shared/lib/api-client';
import type { PageParams, Paginated } from '@/modules/shared/types/api';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// ======================================================================

/** `live` = agente real (billetera de Binance) · `paper` = agente demo (dinero simulado). */
type BotMode = 'paper' | 'live';
type BotStatus = 'running' | 'stopped' | 'paused' | 'error';
type BotTransition = 'start' | 'pause' | 'stop';

/**
 * Qué hace el agente cuando la IA aprueba una operación:
 * - manual   → solo señales con "Analizar ahora"; la orden la creas tú
 * - approval → señal automática por vela; la orden espera tu aprobación
 * - auto     → señal automática por vela; la orden sale sola
 */
type BotExecutionMode = 'manual' | 'approval' | 'auto';

/** En la UI un bot se llama "agente"; la API y los tipos conservan `bot`. */
type Bot = {
	id: number;
	name: string;
	strategy_id: number;
	symbol_id: number;
	timeframe_id: number;
	account_id: number;
	feature_set_id: number | null;
	mode: BotMode;
	status: BotStatus;
	/** JSON libre; hoy incluye `risk_pct` (fracción, 0.01 = 1 %). */
	risk_params: Record<string, unknown>;
	started_at: string | null;
	stopped_at: string | null;
	created_at: string | null;
	execution_mode: BotExecutionMode;
	/** Minutos para aprobar una señal; `null` = valor global del servidor. */
	approval_ttl_minutes: number | null;
	/** Otros usuarios pueden seguir sus señales aprobadas (llegan por Telegram). */
	share_signals: boolean;
	/** Solo agentes demo: monto simulado con el que se creó (DECIMAL como texto). */
	demo_capital: string | null;
};

type BotRiskParams = {
	/** Fracción del capital: 0.01 = 1 %. */
	risk_pct: number;
	max_drawdown_pct?: number;
};

type BotInput = {
	name: string;
	strategy_id: number;
	symbol_id: number;
	timeframe_id: number;
	feature_set_id: number;
	/** Real: opera la billetera de Binance. Demo: exige `demo_capital`. */
	mode: BotMode;
	/** Solo demo: monto simulado a invertir, en la moneda de cotización. */
	demo_capital?: number;
	risk_params: BotRiskParams;
	execution_mode?: BotExecutionMode;
	approval_ttl_minutes?: number | null;
};

/**
 * Renombrar, cambiar el modo de ejecución y compartir señales se puede en
 * cualquier estado; el riesgo solo con el bot detenido. Real o demo no cambia.
 */
type BotUpdate = {
	name?: string;
	risk_params?: BotRiskParams;
	execution_mode?: BotExecutionMode;
	approval_ttl_minutes?: number | null;
	share_signals?: boolean;
};

/**
 * Agente que comparte sus señales, tal como lo ve cualquier usuario
 * (GET /bots/shared): sin nombre, cuenta ni dueño.
 */
type SharedBot = {
	id: number;
	strategy_id: number;
	strategy_name: string | null;
	symbol_id: number;
	symbol: string | null;
	timeframe_id: number;
	timeframe: string | null;
	mode: BotMode;
	status: BotStatus;
	subscribers_count: number;
	/** El usuario ya lo sigue. */
	is_subscribed: boolean;
	/** Es un agente del usuario (no puede seguirlo). */
	is_mine: boolean;
};

/**
 * Evento del historial de un agente (GET /bots/{id}/history).
 * - BOT_CREATED: `data = {mode, execution_mode, risk_pct}`
 * - BOT_UPDATED: `data = {changes: {campo: [antes, después]}}`
 * - BOT_STATUS_CHANGED: `data = {from, to, reason?}`; `reason` solo cuando
 *   lo cambió el sistema (drawdown máximo, cuenta del dueño desactivada).
 */
type BotHistoryEventType = 'BOT_CREATED' | 'BOT_UPDATED' | 'BOT_STATUS_CHANGED';

type BotHistoryEntry = {
	id: number;
	event_type: BotHistoryEventType;
	ts: string | null;
	data: Record<string, unknown>;
	user_id: number | null;
	/** Quién actuó; `null` = el sistema. */
	user_name: string | null;
};

/** Respuesta de seguir / dejar de seguir un agente. */
type BotSubscription = {
	bot_id: number;
	is_subscribed: boolean;
	subscribers_count: number;
};

type BotFilters = {
	account_id?: number;
	/** Real (`live`) o demo (`paper`). */
	mode?: BotMode;
	/** Solo los bots de mis cuentas (para admin, que sin filtro ve todos). */
	mine?: boolean;
};

type SignalAction = 'buy' | 'sell' | 'hold';

/** Estado de la decisión de ejecución (solo BUY/SELL aprobadas de agentes approval/auto). */
type SignalDecisionStatus =
	| 'not_required'
	| 'pending'
	| 'executing'
	| 'executed'
	| 'rejected'
	| 'expired'
	| 'failed';

type SignalDecisionChannel = 'app' | 'telegram' | 'auto';

/** Códigos con los que el agente explica por qué rechazó la operación. */
type SignalRejectionReason =
	| 'REGIME_MISMATCH'
	| 'RULES_NOT_MET'
	| 'LLM_REJECTED'
	| 'INCONSISTENT_LEVELS'
	| 'ENTRY_TOO_FAR'
	| 'RR_RATIO_TOO_LOW';

type SignalRuleDetail = {
	indicator: string;
	operator: string;
	threshold: unknown;
	actual_value: unknown;
	passed: boolean;
};

/** Resultado completo del análisis del agente (JSON libre en el backend). */
type SignalReasons = {
	decision?: 'APPROVED' | 'REJECTED';
	rejection_reason?: SignalRejectionReason | string | null;
	reasoning?: string;
	regime_check_passed?: boolean;
	rules_check_passed?: boolean;
	rr_check_passed?: boolean;
	rules_detail?: SignalRuleDetail[];
	meta?: Record<string, unknown>;
	[key: string]: unknown;
};

/**
 * Las señales llegan con precios y ratios como `number` (el backend los
 * convierte a float al serializar), no como string.
 */
type Signal = {
	id: number;
	bot_id: number;
	ts: string | null;
	action: SignalAction;
	approved: boolean;
	/** 0–1. */
	confidence: number | null;
	entry_price: number | null;
	stop_loss: number | null;
	take_profit: number | null;
	position_size: number | null;
	rr_ratio: number | null;
	/** Servicio de IA que respondió (`groq`, `gemini`, `ollama`); `null` si se rechazó antes de consultarla. */
	llm_provider: string | null;
	llm_model: string | null;
	/** Duración de la consulta a la IA en ms (incluye los servicios que fallaron antes). */
	llm_latency_ms: number | null;
	reasons: SignalReasons;
	created_at: string | null;
	decision_status: SignalDecisionStatus;
	/** Límite para aprobarla (solo pendientes). */
	expires_at: string | null;
	decided_at: string | null;
	decision_channel: SignalDecisionChannel | null;
	/** Código del fallo si se aprobó pero no se pudo ejecutar. */
	decision_reason: string | null;
	/** El mismo fallo en texto para mostrar (lo traduce el backend). */
	decision_reason_message: string | null;
	/** Vela cerrada que la originó (señales automáticas). */
	candle_ts: string | null;
};

/** Señal por aprobar con el agente al que pertenece (GET /signals/pending). */
type PendingSignal = Signal & {
	bot_name: string;
	bot_mode: BotMode;
};

type SignalDecisionResult = {
	signal_id: number;
	bot_id: number;
	decision_status: SignalDecisionStatus;
	decision_channel: SignalDecisionChannel | null;
	decided_at: string | null;
	order_id: number | null;
	order_status: string | null;
};

type SignalFilters = {
	bot_id: number;
	action?: SignalAction;
	limit?: number;
};

/** Filtros de `listSignalsPage` (`limit` no aplica: manda `page_size`). */
type SignalPageFilters = Omit<SignalFilters, 'limit'>;

// ======================================================================
// Bots
// ======================================================================

/**
 * Usuario: siempre sus bots (con `account_id`, solo los de esa cuenta).
 * Admin: sin filtro devuelve todos; con `mine`, solo los suyos.
 */
function listBots(filters: BotFilters = {}) {
	return api.get<Bot[]>('/bots', filters);
}

/** Igual que `listBots`, página a página (el más reciente primero). */
function getBot(id: number) {
	return api.get<Bot>(`/bots/${id}`);
}

function createBot(input: BotInput) {
	return api.post<Bot>('/bots', input);
}

function updateBot(id: number, input: BotUpdate) {
	return api.put<Bot>(`/bots/${id}`, input);
}

/** `start`: detenido → activo · `pause`: activo → pausado · `stop`: → detenido. */
function transitionBot(id: number, transition: BotTransition) {
	return api.post<Bot>(`/bots/${id}/${transition}`);
}

/** Quién creó, editó, inició, pausó o detuvo el agente (el más reciente primero). */
function listBotHistory(id: number, page: PageParams) {
	return api.get<Paginated<BotHistoryEntry>>(`/bots/${id}/history`, page);
}

/** Sin conjunto de indicadores, `rows_calculated` llega en null. */
type BotMarketSyncResult = {
	rows_fetched: number;
	rows_calculated: number | null;
};

/** Descarga las velas del agente y recalcula sus indicadores (puede tardar). */
function syncBotMarket(id: number) {
	return api.post<BotMarketSyncResult>(`/bots/${id}/market/sync`);
}

// ======================================================================
// Señales compartidas (suscripciones)
// ======================================================================

/** Agentes de cualquier usuario que comparten sus señales. */
function listSharedBots() {
	return api.get<SharedBot[]>('/bots/shared');
}

/** Idempotente. Exige Telegram vinculado: es el único canal de envío. */
function subscribeToBot(id: number) {
	return api.post<BotSubscription>(`/bots/${id}/subscription`);
}

/** Idempotente. */
function unsubscribeFromBot(id: number) {
	return api.delete<BotSubscription>(`/bots/${id}/subscription`);
}

// ======================================================================
// Señales
// ======================================================================

/** El backend las devuelve de la más reciente a la más antigua. */
function listSignals(filters: SignalFilters) {
	return api.get<Signal[]>('/signals', filters);
}

/** Señales de un agente página a página (la más reciente primero). */
function listSignalsPage(filters: SignalPageFilters, page: PageParams) {
	return api.get<Paginated<Signal>>('/signals', { ...filters, ...page });
}

/** Analiza el mercado con la IA (puede tardar). El bot debe estar activo. */
function generateSignal(botId: number) {
	return api.post<Signal>('/signals/generate', { bot_id: botId });
}

/** Señales de mis agentes que esperan aprobación (las vencidas no llegan). */
function listPendingSignals() {
	return api.get<PendingSignal[]>('/signals/pending');
}

/** Aprueba: el servidor revalida al precio actual y envía la orden. */
function approveSignal(signalId: number) {
	return api.post<SignalDecisionResult>(`/signals/${signalId}/approve`);
}

function rejectSignal(signalId: number) {
	return api.post<SignalDecisionResult>(`/signals/${signalId}/reject`);
}

export type {
	Bot,
	BotExecutionMode,
	BotFilters,
	BotHistoryEntry,
	BotHistoryEventType,
	BotInput,
	BotMarketSyncResult,
	BotMode,
	BotRiskParams,
	BotStatus,
	BotSubscription,
	BotTransition,
	BotUpdate,
	PendingSignal,
	SharedBot,
	Signal,
	SignalAction,
	SignalDecisionChannel,
	SignalDecisionResult,
	SignalDecisionStatus,
	SignalFilters,
	SignalPageFilters,
	SignalReasons,
	SignalRejectionReason,
	SignalRuleDetail,
};
export {
	approveSignal,
	createBot,
	generateSignal,
	getBot,
	listBotHistory,
	listBots,
	listPendingSignals,
	listSharedBots,
	listSignals,
	listSignalsPage,
	rejectSignal,
	subscribeToBot,
	syncBotMarket,
	transitionBot,
	unsubscribeFromBot,
	updateBot,
};
