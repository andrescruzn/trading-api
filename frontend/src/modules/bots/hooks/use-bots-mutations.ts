import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	approveSignal,
	type BotInput,
	type BotTransition,
	type BotUpdate,
	createBot,
	generateSignal,
	rejectSignal,
	transitionBot,
	updateBot,
} from '@/modules/bots/api/bots.api';
import {
	BOTS_QUERY_KEY,
	SIGNALS_QUERY_KEY,
} from '@/modules/bots/hooks/use-bots-queries';
import {
	FILLS_QUERY_KEY,
	ORDERS_QUERY_KEY,
	POSITIONS_QUERY_KEY,
} from '@/modules/orders/hooks/use-orders-queries';

function useCreateBotMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: BotInput) => createBot(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: BOTS_QUERY_KEY }),
	});
}

function useUpdateBotMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({ id, input }: { id: number; input: BotUpdate }) =>
			updateBot(id, input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: BOTS_QUERY_KEY }),
	});
}

function useTransitionBotMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({
			id,
			transition,
		}: {
			id: number;
			transition: BotTransition;
		}) => transitionBot(id, transition),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: BOTS_QUERY_KEY }),
	});
}

function useGenerateSignalMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (botId: number) => generateSignal(botId),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: SIGNALS_QUERY_KEY }),
	});
}

/**
 * Aprobar envía una orden: además de las señales se refrescan órdenes,
 * ejecuciones y posiciones. Se invalida también si falla (la señal pudo
 * quedar como no ejecutada o vencida).
 */
function useApproveSignalMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (signalId: number) => approveSignal(signalId),
		onSettled: () => {
			for (const queryKey of [
				SIGNALS_QUERY_KEY,
				ORDERS_QUERY_KEY,
				FILLS_QUERY_KEY,
				POSITIONS_QUERY_KEY,
			]) {
				queryClient.invalidateQueries({ queryKey });
			}
		},
	});
}

function useRejectSignalMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (signalId: number) => rejectSignal(signalId),
		onSettled: () =>
			queryClient.invalidateQueries({ queryKey: SIGNALS_QUERY_KEY }),
	});
}

export {
	useApproveSignalMutation,
	useCreateBotMutation,
	useGenerateSignalMutation,
	useRejectSignalMutation,
	useTransitionBotMutation,
	useUpdateBotMutation,
};
