import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// ======================================================================

type ExchangeType = 'crypto_exchange' | 'broker' | 'data_vendor';
type AssetClass = 'crypto' | 'metal' | 'etf' | 'stock' | 'forex';

type Exchange = {
	id: number;
	name: string;
	type: ExchangeType;
	is_active: boolean;
	created_at: string | null;
};

type MarketSymbol = {
	id: number;
	exchange_id: number;
	exchange_name: string | null;
	symbol: string;
	asset_class: AssetClass;
	base_asset: string | null;
	quote_asset: string | null;
	tick_size: string | null;
	lot_size: string | null;
	is_active: boolean;
	created_at: string | null;
};

type Timeframe = {
	id: number;
	code: string;
	seconds: number;
};

/** Precios y volumen llegan como string (DECIMAL del backend). */
type Candle = {
	id: number;
	symbol_id: number;
	timeframe_id: number;
	ts: string;
	open: string;
	high: string;
	low: string;
	close: string;
	volume: string;
};

type FetchCandlesResult = {
	exchange: string;
	symbol: string;
	timeframe: string;
	rows_fetched: number;
	rows_affected?: number;
};

type ExchangeInput = { name: string; type: ExchangeType };
type ExchangeUpdate = Partial<ExchangeInput> & { is_active?: boolean };

type SymbolInput = {
	exchange_id: number;
	symbol: string;
	asset_class: AssetClass;
	base_asset?: string | null;
	quote_asset?: string | null;
	tick_size?: string | null;
	lot_size?: string | null;
};
type SymbolUpdate = Partial<Omit<SymbolInput, 'exchange_id' | 'symbol'>> & {
	is_active?: boolean;
};

type TimeframeInput = { code: string; seconds: number };

type SymbolFilters = {
	exchange_id?: number;
	asset_class?: AssetClass;
	is_active?: boolean;
};

type CandleFilters = {
	symbol_id: number;
	timeframe_id: number;
	limit?: number;
};

// ======================================================================
// Exchanges
// ======================================================================

function listExchanges(filters: { is_active?: boolean } = {}) {
	return api.get<Exchange[]>('/exchanges', filters);
}

function createExchange(input: ExchangeInput) {
	return api.post<Exchange>('/exchanges', input);
}

function updateExchange(id: number, input: ExchangeUpdate) {
	return api.put<Exchange>(`/exchanges/${id}`, input);
}

// ======================================================================
// Símbolos
// ======================================================================

function listSymbols(filters: SymbolFilters = {}) {
	return api.get<MarketSymbol[]>('/symbols', filters);
}

function createSymbol(input: SymbolInput) {
	return api.post<MarketSymbol>('/symbols', input);
}

function updateSymbol(id: number, input: SymbolUpdate) {
	return api.put<MarketSymbol>(`/symbols/${id}`, input);
}

// ======================================================================
// Timeframes
// ======================================================================

function listTimeframes() {
	return api.get<Timeframe[]>('/timeframes');
}

function createTimeframe(input: TimeframeInput) {
	return api.post<Timeframe>('/timeframes', input);
}

// ======================================================================
// Velas
// ======================================================================

/** El backend las devuelve de la más reciente a la más antigua. */
function listCandles(filters: CandleFilters) {
	return api.get<Candle[]>('/candles', filters);
}

/** Descarga velas del exchange real (ccxt) y las guarda. Solo admin. */
function fetchCandles(input: CandleFilters) {
	return api.post<FetchCandlesResult>('/candles/fetch', input);
}

export type {
	AssetClass,
	Candle,
	CandleFilters,
	Exchange,
	ExchangeInput,
	ExchangeType,
	ExchangeUpdate,
	FetchCandlesResult,
	MarketSymbol,
	SymbolFilters,
	SymbolInput,
	SymbolUpdate,
	Timeframe,
	TimeframeInput,
};
export {
	createExchange,
	createSymbol,
	createTimeframe,
	fetchCandles,
	listCandles,
	listExchanges,
	listSymbols,
	listTimeframes,
	updateExchange,
	updateSymbol,
};
