import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	createExchange,
	createSymbol,
	createTimeframe,
	type ExchangeInput,
	type ExchangeUpdate,
	refreshExplorer,
	type SymbolInput,
	type SymbolUpdate,
	type TimeframeInput,
	updateExchange,
	updateSymbol,
} from '@/modules/market/api/market.api';
import {
	CANDLES_QUERY_KEY,
	EXCHANGES_QUERY_KEY,
	EXPLORER_QUERY_KEY,
	SYMBOLS_QUERY_KEY,
	TIMEFRAMES_QUERY_KEY,
} from '@/modules/market/hooks/use-market-queries';

function useCreateExchangeMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: ExchangeInput) => createExchange(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: EXCHANGES_QUERY_KEY }),
	});
}

function useUpdateExchangeMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({ id, input }: { id: number; input: ExchangeUpdate }) =>
			updateExchange(id, input),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: EXCHANGES_QUERY_KEY });
			// El nombre del exchange también se muestra en los símbolos.
			queryClient.invalidateQueries({ queryKey: SYMBOLS_QUERY_KEY });
		},
	});
}

function useCreateSymbolMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: SymbolInput) => createSymbol(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: SYMBOLS_QUERY_KEY }),
	});
}

function useUpdateSymbolMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({ id, input }: { id: number; input: SymbolUpdate }) =>
			updateSymbol(id, input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: SYMBOLS_QUERY_KEY }),
	});
}

function useCreateTimeframeMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: TimeframeInput) => createTimeframe(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: TIMEFRAMES_QUERY_KEY }),
	});
}

function useRefreshExplorerMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: refreshExplorer,
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: EXPLORER_QUERY_KEY });
			queryClient.invalidateQueries({ queryKey: CANDLES_QUERY_KEY });
		},
	});
}

export {
	useCreateExchangeMutation,
	useCreateSymbolMutation,
	useCreateTimeframeMutation,
	useRefreshExplorerMutation,
	useUpdateExchangeMutation,
	useUpdateSymbolMutation,
};
