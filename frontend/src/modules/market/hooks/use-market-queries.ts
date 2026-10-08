import { keepPreviousData, useQuery } from '@tanstack/react-query';
import {
	type CandleFilters,
	listCandles,
	listExchanges,
	listSymbols,
	listTimeframes,
	type SymbolFilters,
} from '@/modules/market/api/market.api';

const EXCHANGES_QUERY_KEY = ['exchanges'] as const;
const SYMBOLS_QUERY_KEY = ['symbols'] as const;
const TIMEFRAMES_QUERY_KEY = ['timeframes'] as const;
const CANDLES_QUERY_KEY = ['candles'] as const;

// Catálogos casi estáticos: se cachean un rato para no repetir la petición en
// cada página que los usa como opciones de un select.
const CATALOG_STALE_TIME = 5 * 60 * 1000;

function useExchangesQuery(filters: { is_active?: boolean } = {}) {
	return useQuery({
		queryKey: [...EXCHANGES_QUERY_KEY, filters],
		queryFn: () => listExchanges(filters),
		staleTime: CATALOG_STALE_TIME,
	});
}

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

export {
	CANDLES_QUERY_KEY,
	EXCHANGES_QUERY_KEY,
	SYMBOLS_QUERY_KEY,
	TIMEFRAMES_QUERY_KEY,
	useCandlesQuery,
	useExchangesQuery,
	useSymbolsQuery,
	useTimeframesQuery,
};
