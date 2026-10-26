import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	createSymbol,
	createTimeframe,
	refreshExplorer,
	type SymbolInput,
	type SymbolUpdate,
	type TimeframeInput,
	updateSymbol,
} from '@/modules/market/api/market.api';
import {
	CANDLES_QUERY_KEY,
	EXPLORER_QUERY_KEY,
	SYMBOLS_QUERY_KEY,
	TIMEFRAMES_QUERY_KEY,
} from '@/modules/market/hooks/use-market-queries';

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
	useCreateSymbolMutation,
	useCreateTimeframeMutation,
	useRefreshExplorerMutation,
	useUpdateSymbolMutation,
};
