import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	type BotInput,
	type BotTransition,
	createBot,
	generateSignal,
	transitionBot,
} from '@/modules/bots/api/bots.api';
import {
	BOTS_QUERY_KEY,
	SIGNALS_QUERY_KEY,
} from '@/modules/bots/hooks/use-bots-queries';

function useCreateBotMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: BotInput) => createBot(input),
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

export {
	useCreateBotMutation,
	useGenerateSignalMutation,
	useTransitionBotMutation,
};
