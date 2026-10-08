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
	Fill,
	FillFilters,
	Order,
	OrderFilters,
	OrderInput,
	OrderSide,
	OrderStatus,
	OrderType,
	Position,
	TimeInForce,
};
export { createOrder, getOrder, listFills, listOrders, listPositions };
