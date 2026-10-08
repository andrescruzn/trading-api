import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	type AlertRuleInput,
	type AlertRuleUpdate,
	createAlertRule,
	sendTelegramTest,
	updateAlertRule,
} from '@/modules/alerts/api/alerts.api';
import { ALERT_RULES_QUERY_KEY } from '@/modules/alerts/hooks/use-alerts-queries';

function useCreateAlertRuleMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: AlertRuleInput) => createAlertRule(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: ALERT_RULES_QUERY_KEY }),
	});
}

function useUpdateAlertRuleMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({ id, input }: { id: number; input: AlertRuleUpdate }) =>
			updateAlertRule(id, input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: ALERT_RULES_QUERY_KEY }),
	});
}

function useSendTelegramTestMutation() {
	return useMutation({ mutationFn: sendTelegramTest });
}

export {
	useCreateAlertRuleMutation,
	useSendTelegramTestMutation,
	useUpdateAlertRuleMutation,
};
