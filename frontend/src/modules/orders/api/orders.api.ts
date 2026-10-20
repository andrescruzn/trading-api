import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
//
// Órdenes, posiciones y ejecuciones llegan con cantidades y precios como
// `number` (el backend los convierte a float al serializar). Al crear una
// orden se envían como string para no perder precisión (Pydantic `Decimal`).
// ======================================================================

type OrderSide = 'buy' | 'sell';
type OrderType = 'market' | 'limit' | 'stop' | 'stop_limit';
type OrderStatus =
	| 'new'
	| 'sent'
	| 'partially_filled'
	| 'filled'
	| 'canceled'
	| 'rejected';
type TimeInForce = 'GTC' | 'IOC' | 'FOK';

type Order = {
	id: number;
	bot_id: number;
	signal_id: number | null;
	exchange_order_id: string | null;
	side: OrderSide;
	type: OrderType;
	status: OrderStatus;
	qty: number;
	price: number | null;
	stop_price: number | null;
	time_in_force: TimeInForce | null;
	meta: Record<string, unknown> | null;
	ts: string | null;
	created_at: string | null;
};

type Position = {
	id: number;
	bot_id: number;
	symbol_id: number;
	qty: number;
	avg_price: number | null;
	realized_pnl: number | null;
	/** `true` si la posición está en cero (sin exposición). */
	is_flat: boolean;
	updated_at: string | null;
	/** Niveles que vigila el scheduler (posición abierta desde una señal aprobada). */
	stop_loss: number | null;
	take_profit: number | null;
	signal_id: number | null;
	/** Orden stop loss nativa en el exchange (live); `null` = la vigila el scheduler. */
	sl_order_id: number | null;
};

type Fill = {
	id: number;
	order_id: number;
	exchange_trade_id: string | null;
	qty: number;
	price: number;
	fee: number | null;
	fee_asset: string | null;
	/** `qty × price`. */
	notional_value: number | null;
	ts: string | null;
	created_at: string | null;
};

type OrderInput = {
	bot_id: number;
	side: OrderSide;
	type: OrderType;
	qty: string;
	/** Obligatorio en `limit` y `stop_limit`. */
	price?: string;
	/** Obligatorio en `stop` y `stop_limit`. */
	stop_price?: string;
	time_in_force?: TimeInForce;
	signal_id?: number;
	/** Protección automática de la posición: solo compras a mercado. */
	stop_loss?: string;
	take_profit?: string;
};

/** `GET /performance?bot_id=`: fracciones (0.6 = 60 %) y montos en la cotización. */
type ClosedTrade = {
	opened_at: string | null;
	closed_at: string | null;
	qty: number;
	cost: number;
	pnl: number;
	return_pct: number | null;
};

type BotPerformance = {
	trades: number;
	wins: number;
	losses: number;
	win_rate: number | null;
	realized_pnl: number;
	gross_profit: number;
	gross_loss: number;
	profit_factor: number | null;
	avg_win: number | null;
	avg_loss: number | null;
	/** R/R real: ganancia media / pérdida media. */
	payoff_ratio: number | null;
	avg_return_pct: number | null;
	max_drawdown: number;
	total_fees: number;
	open_qty: number;
	open_avg_price: number | null;
	open_realized_pnl: number;
	last_price: number | null;
	unrealized_pnl: number | null;
	equity_curve: { ts: string | null; pnl: number }[];
	/** La más reciente primero. */
	closed_trades: ClosedTrade[];
};

/** `GET /performance/strategies`: anónimo, en retornos % por operación. */
type StrategyTrackRecord = {
	strategy_id: number;
	strategy_name: string;
	mode: 'paper' | 'live';
	agents: number;
	trades: number;
	wins: number;
	win_rate: number | null;
	avg_return_pct: number | null;
	total_return_pct: number;
	profit_factor: number | null;
	max_drawdown_pct: number;
	best_trade_pct: number | null;
	worst_trade_pct: number | null;
	curve: { ts: string | null; return_pct: number }[];
};

type OrderFilters = {
	bot_id?: number;
	/** 1–500 (por defecto 100). */
	limit?: number;
};

type FillFilters = {
	order_id?: number;
	bot_id?: number;
	limit?: number;
};

// ======================================================================
// Órdenes
// ======================================================================

/** Usuario: el backend exige `bot_id`. Admin: sin filtro devuelve todas. */
function listOrders(filters: OrderFilters = {}) {
	return api.get<Order[]>('/orders', filters);
}

function getOrder(id: number) {
	return api.get<Order>(`/orders/${id}`);
}

/** Crea y ejecuta la orden al instante (paper o live según el bot). */
function createOrder(input: OrderInput) {
	return api.post<Order>('/orders', input);
}

/** Cancela una orden live abierta; devuelve cómo quedó tras sincronizarla. */
function cancelOrder(id: number) {
	return api.post<Order>(`/orders/${id}/cancel`);
}

// ======================================================================
// Rendimiento
// ======================================================================

function getBotPerformance(botId: number) {
	return api.get<BotPerformance>('/performance', { bot_id: botId });
}

function listStrategyTrackRecord(filters: { mode?: 'paper' | 'live' } = {}) {
	return api.get<StrategyTrackRecord[]>('/performance/strategies', filters);
}

// ======================================================================
// Posiciones y ejecuciones
// ======================================================================

/** Usuario: el backend exige `bot_id`. Admin: sin filtro devuelve todas. */
function listPositions(filters: { bot_id?: number } = {}) {
	return api.get<Position[]>('/positions', filters);
}

/** Requiere `order_id` o `bot_id`. */
function listFills(filters: FillFilters) {
	return api.get<Fill[]>('/fills', filters);
}

export type {
	BotPerformance,
	ClosedTrade,
	Fill,
	FillFilters,
	Order,
	OrderFilters,
	OrderInput,
	OrderSide,
	OrderStatus,
	OrderType,
	Position,
	StrategyTrackRecord,
	TimeInForce,
};
export {
	cancelOrder,
	createOrder,
	getBotPerformance,
	getOrder,
	listFills,
	listOrders,
	listPositions,
	listStrategyTrackRecord,
};
