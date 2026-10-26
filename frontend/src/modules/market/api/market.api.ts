import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// ======================================================================

type AssetClass =
	| 'crypto'
	| 'metal'
	| 'commodity'
	| 'index'
	| 'etf'
	| 'stock'
	| 'forex';

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
	/** `true` si sus velas se descargan solas (exchange soportado). */
	supports_auto_fetch: boolean;
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

type TrendDirection = 'up' | 'down' | 'sideways';

/**
 * Fila del explorador de tendencia (velas 1d). Sin velas suficientes,
 * `has_data` es `false` y las métricas llegan en `null`.
 */
type TrendExplorerRow = {
	symbol_id: number;
	symbol: string;
	exchange_name: string | null;
	asset_class: AssetClass;
	/** Contrato perpetuo (`XAU/USDT:USDT`): solo se opera en paper. */
	is_perpetual: boolean;
	has_data: boolean;
	candles: number;
	last_close: number | null;
	last_ts: string | null;
	/** Rendimientos como fracción (`0.05` = 5 %). */
	ret_30d: number | null;
	ret_90d: number | null;
	adx_14: number | null;
	/** Eficiencia de Kaufman en 30 días, de 0 a 1. */
	efficiency_30: number | null;
	/** ATR de 14 días sobre el cierre, como fracción. */
	atr_pct_14: number | null;
	direction: TrendDirection | null;
	/** Fuerza de tendencia de 0 a 100. */
	strength: number | null;
	/** Fuerza con signo según la dirección: ordena el ranking. */
	score: number | null;
};

type RefreshExplorerResult = {
	updated: string[];
	skipped: string[];
	failed: { symbol: string; code: string }[];
};

/** El exchange no se envía: el backend lo crea siempre en Binance. */
type SymbolInput = {
	symbol: string;
	asset_class: AssetClass;
	base_asset?: string | null;
	quote_asset?: string | null;
	tick_size?: string | null;
	lot_size?: string | null;
};
type SymbolUpdate = Partial<Omit<SymbolInput, 'symbol'>> & {
	is_active?: boolean;
};

type TimeframeInput = { code: string; seconds: number };

type SymbolFilters = {
	asset_class?: AssetClass;
	is_active?: boolean;
};

type CandleFilters = {
	symbol_id: number;
	timeframe_id: number;
	limit?: number;
};

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

// ======================================================================
// Explorador de tendencia
// ======================================================================

function listTrendExplorer(filters: { asset_class?: AssetClass } = {}) {
	return api.get<TrendExplorerRow[]>('/explorer', filters);
}

/** Descarga las velas diarias de todos los símbolos. Solo admin. */
function refreshExplorer() {
	return api.post<RefreshExplorerResult>('/explorer/refresh');
}

export type {
	AssetClass,
	Candle,
	CandleFilters,
	MarketSymbol,
	RefreshExplorerResult,
	SymbolFilters,
	SymbolInput,
	SymbolUpdate,
	Timeframe,
	TimeframeInput,
	TrendDirection,
	TrendExplorerRow,
};
export {
	createSymbol,
	createTimeframe,
	listCandles,
	listSymbols,
	listTimeframes,
	listTrendExplorer,
	refreshExplorer,
	updateSymbol,
};
