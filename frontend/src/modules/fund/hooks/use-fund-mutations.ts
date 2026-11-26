import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	assignUnclaimedDeposit,
	cancelDeposit,
	confirmDeposit,
	createDeposit,
	type DepositInput,
	type FundSettingsInput,
	type NetworkChoice,
	refundPending,
	rejectDeposit,
	setDepositNetworks,
	updateFundSettings,
	verifyDeposits,
} from '@/modules/fund/api/fund.api';
import {
	DEPOSIT_INFO_QUERY_KEY,
	DEPOSITS_QUERY_KEY,
	FUND_SETTINGS_QUERY_KEY,
	LEDGER_QUERY_KEY,
	MY_BALANCES_QUERY_KEY,
	PARTICIPANTS_QUERY_KEY,
	UNCLAIMED_QUERY_KEY,
} from '@/modules/fund/hooks/use-fund-queries';

/** Lo que cambia cuando se mueve dinero: depósitos, saldos y libros. */
function useInvalidateMoney() {
	const queryClient = useQueryClient();
	return () =>
		Promise.all(
			[
				DEPOSITS_QUERY_KEY,
				UNCLAIMED_QUERY_KEY,
				MY_BALANCES_QUERY_KEY,
				LEDGER_QUERY_KEY,
				PARTICIPANTS_QUERY_KEY,
			].map((queryKey) => queryClient.invalidateQueries({ queryKey })),
		);
}

function useInvalidateSettings() {
	const queryClient = useQueryClient();
	return () =>
		Promise.all(
			[FUND_SETTINGS_QUERY_KEY, DEPOSIT_INFO_QUERY_KEY].map((queryKey) =>
				queryClient.invalidateQueries({ queryKey }),
			),
		);
}

function useUpdateFundSettingsMutation() {
	const invalidate = useInvalidateSettings();
	return useMutation({
		mutationFn: (input: FundSettingsInput) => updateFundSettings(input),
		onSuccess: invalidate,
	});
}

function useSetDepositNetworksMutation() {
	const invalidate = useInvalidateSettings();
	return useMutation({
		mutationFn: (networks: NetworkChoice[]) => setDepositNetworks(networks),
		onSuccess: invalidate,
	});
}

function useCreateDepositMutation() {
	const invalidate = useInvalidateMoney();
	return useMutation({
		mutationFn: (input: DepositInput) => createDeposit(input),
		onSuccess: invalidate,
	});
}

function useCancelDepositMutation() {
	const invalidate = useInvalidateMoney();
	return useMutation({
		mutationFn: (id: number) => cancelDeposit(id),
		onSuccess: invalidate,
	});
}

function useConfirmDepositMutation() {
	const invalidate = useInvalidateMoney();
	return useMutation({
		mutationFn: ({
			id,
			amount,
			note,
		}: {
			id: number;
			amount?: string | null;
			note?: string | null;
		}) => confirmDeposit(id, { amount, note }),
		onSuccess: invalidate,
	});
}

function useRejectDepositMutation() {
	const invalidate = useInvalidateMoney();
	return useMutation({
		mutationFn: ({ id, note }: { id: number; note: string }) =>
			rejectDeposit(id, note),
		onSuccess: invalidate,
	});
}

function useVerifyDepositsMutation() {
	const invalidate = useInvalidateMoney();
	return useMutation({ mutationFn: verifyDeposits, onSuccess: invalidate });
}

function useAssignUnclaimedMutation() {
	const invalidate = useInvalidateMoney();
	return useMutation({
		mutationFn: assignUnclaimedDeposit,
		onSuccess: invalidate,
	});
}

function useRefundPendingMutation() {
	const invalidate = useInvalidateMoney();
	return useMutation({
		mutationFn: ({
			userId,
			amount,
			reason,
		}: {
			userId: number;
			amount: string;
			reason: string;
		}) => refundPending(userId, { amount, reason }),
		onSuccess: invalidate,
	});
}

export {
	useAssignUnclaimedMutation,
	useCancelDepositMutation,
	useConfirmDepositMutation,
	useCreateDepositMutation,
	useRefundPendingMutation,
	useRejectDepositMutation,
	useSetDepositNetworksMutation,
	useUpdateFundSettingsMutation,
	useVerifyDepositsMutation,
};
