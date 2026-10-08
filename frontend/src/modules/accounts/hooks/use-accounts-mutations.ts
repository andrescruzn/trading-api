import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	type AccountInput,
	type AccountUpdate,
	type BalanceInput,
	createAccount,
	recordBalance,
	updateAccount,
} from '@/modules/accounts/api/accounts.api';
import {
	ACCOUNT_BALANCES_QUERY_KEY,
	ACCOUNTS_QUERY_KEY,
} from '@/modules/accounts/hooks/use-accounts-queries';

function useCreateAccountMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: AccountInput) => createAccount(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: ACCOUNTS_QUERY_KEY }),
	});
}

function useUpdateAccountMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({ id, input }: { id: number; input: AccountUpdate }) =>
			updateAccount(id, input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: ACCOUNTS_QUERY_KEY }),
	});
}

function useRecordBalanceMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({
			accountId,
			input,
		}: {
			accountId: number;
			input: BalanceInput;
		}) => recordBalance(accountId, input),
		onSuccess: (_balance, { accountId }) =>
			queryClient.invalidateQueries({
				queryKey: [...ACCOUNT_BALANCES_QUERY_KEY, accountId],
			}),
	});
}

export {
	useCreateAccountMutation,
	useRecordBalanceMutation,
	useUpdateAccountMutation,
};
