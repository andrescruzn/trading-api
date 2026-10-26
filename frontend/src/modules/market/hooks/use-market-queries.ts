import { keepPreviousData, useQuery } from '@tanstack/react-query';
import {
	type AssetClass,
	type CandleFilters,
	listCandles,
	listSymbols,
	listTimeframes,
	listTrendExplorer,
	type SymbolFilters,
} from '@/modules/market/api/market.api';

const SYMBOLS_QUERY_KEY = ['symbols'] as const;
const TIMEFRAMES_QUERY_KEY = ['timeframes'] as const;
const CANDLES_QUERY_KEY = ['candles'] as const;
const EXPLORER_QUERY_KEY = ['explorer'] as const;

// Catálogos casi estáticos: se cachean un rato para no repetir la petición en
// cada página que los usa como opciones de un select.
const CATALOG_STALE_TIME = 5 * 60 * 1000;

function useSymbolsQuery(filters: SymbolFilters = {}) {
	return useQuery({
		queryKey: [...SYMBOLS_QUERY_KEY, filters],
		queryFn: () => listSymbols(filters),
		placeholderData: keepPreviousData,
		staleTime: CATALOG_STALE_TIME,
	});
}

function useTimeframesQuery() {
	return useQuery({
		queryKey: TIMEFRAMES_QUERY_KEY,
		queryFn: listTimeframes,
		staleTime: CATALOG_STALE_TIME,
	});
}

/** Solo consulta cuando hay símbolo y timeframe elegidos. */
function useCandlesQuery(filters: Partial<CandleFilters>) {
	const { symbol_id, timeframe_id, limit } = filters;
	return useQuery({
		queryKey: [...CANDLES_QUERY_KEY, { symbol_id, timeframe_id, limit }],
		queryFn: () =>
			listCandles({
				symbol_id: symbol_id as number,
				timeframe_id: timeframe_id as number,
				limit,
			}),
		enabled: !!symbol_id && !!timeframe_id,
		placeholderData: keepPreviousData,
	});
}

/** Las métricas salen de velas diarias: no cambian de un minuto a otro. */
function useTrendExplorerQuery(filters: { asset_class?: AssetClass } = {}) {
	return useQuery({
		queryKey: [...EXPLORER_QUERY_KEY, filters],
		queryFn: () => listTrendExplorer(filters),
		placeholderData: keepPreviousData,
		staleTime: CATALOG_STALE_TIME,
	});
}

export {
	CANDLES_QUERY_KEY,
	EXPLORER_QUERY_KEY,
	SYMBOLS_QUERY_KEY,
	TIMEFRAMES_QUERY_KEY,
	useCandlesQuery,
	useSymbolsQuery,
	useTimeframesQuery,
	useTrendExplorerQuery,
};
