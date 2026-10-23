import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { ReceiptFile } from '@/modules/fund/api/fund-overview.api';
import {
	attachWithdrawalReceipt,
	cancelRedemption,
	cancelWithdrawal,
	createFeeSchedule,
	createPayoutMethod,
	createWithdrawal,
	deactivatePayoutMethod,
	payWithdrawal,
	rejectWithdrawal,
	requestRedemption,
	setCommissionShares,
} from '@/modules/fund/api/fund-payouts.api';
import {
	FUND_OVERVIEW_QUERY_KEY,
	MY_SUMMARY_QUERY_KEY,
} from '@/modules/fund/hooks/use-fund-overview-queries';
import {
	COMMISSION_SHARES_QUERY_KEY,
	FEE_SCHEDULE_QUERY_KEY,
	MY_COMMISSIONS_QUERY_KEY,
	MY_REDEMPTIONS_QUERY_KEY,
	OWNER_EARNINGS_QUERY_KEY,
	PAYOUT_METHODS_QUERY_KEY,
	WITHDRAWABLE_QUERY_KEY,
	WITHDRAWALS_QUERY_KEY,
} from '@/modules/fund/hooks/use-fund-payouts-queries';
import {
	PARTICIPATIONS_QUERY_KEY,
	POOLS_QUERY_KEY,
	SETTLEMENT_PREVIEW_QUERY_KEY,
} from '@/modules/fund/hooks/use-fund-pools-queries';
import {
	LEDGER_QUERY_KEY,
	MY_BALANCES_QUERY_KEY,
	PARTICIPANTS_QUERY_KEY,
} from '@/modules/fund/hooks/use-fund-queries';

function useInvalidate(keys: readonly (readonly string[])[]) {
	const queryClient = useQueryClient();
	return () =>
		Promise.all(
			keys.map((queryKey) => queryClient.invalidateQueries({ queryKey })),
		);
}

// Lo que cambia cuando se mueve dinero hacia afuera
const MONEY_KEYS = [
	WITHDRAWALS_QUERY_KEY,
	WITHDRAWABLE_QUERY_KEY,
	MY_BALANCES_QUERY_KEY,
	LEDGER_QUERY_KEY,
	PARTICIPANTS_QUERY_KEY,
	FUND_OVERVIEW_QUERY_KEY,
	MY_SUMMARY_QUERY_KEY,
] as const;

const REDEMPTION_KEYS = [
	MY_REDEMPTIONS_QUERY_KEY,
	POOLS_QUERY_KEY,
	SETTLEMENT_PREVIEW_QUERY_KEY,
	PARTICIPATIONS_QUERY_KEY,
] as const;

function useCreateFeeScheduleMutation() {
	const invalidate = useInvalidate([
		FEE_SCHEDULE_QUERY_KEY,
		SETTLEMENT_PREVIEW_QUERY_KEY,
	]);
	return useMutation({ mutationFn: createFeeSchedule, onSuccess: invalidate });
}

function useSetCommissionSharesMutation() {
	const invalidate = useInvalidate([
		COMMISSION_SHARES_QUERY_KEY,
		SETTLEMENT_PREVIEW_QUERY_KEY,
	]);
	return useMutation({
		mutationFn: setCommissionShares,
		onSuccess: invalidate,
	});
}

function useRequestRedemptionMutation() {
	const invalidate = useInvalidate(REDEMPTION_KEYS);
	return useMutation({ mutationFn: requestRedemption, onSuccess: invalidate });
}

function useCancelRedemptionMutation() {
	const invalidate = useInvalidate(REDEMPTION_KEYS);
	return useMutation({
		mutationFn: (id: number) => cancelRedemption(id),
		onSuccess: invalidate,
	});
}

function useCreatePayoutMethodMutation() {
	const invalidate = useInvalidate([PAYOUT_METHODS_QUERY_KEY]);
	return useMutation({ mutationFn: createPayoutMethod, onSuccess: invalidate });
}

function useDeactivatePayoutMethodMutation() {
	const invalidate = useInvalidate([PAYOUT_METHODS_QUERY_KEY]);
	return useMutation({
		mutationFn: (id: number) => deactivatePayoutMethod(id),
		onSuccess: invalidate,
	});
}

function useCreateWithdrawalMutation() {
	const invalidate = useInvalidate(MONEY_KEYS);
	return useMutation({ mutationFn: createWithdrawal, onSuccess: invalidate });
}

function useCancelWithdrawalMutation() {
	const invalidate = useInvalidate(MONEY_KEYS);
	return useMutation({
		mutationFn: (id: number) => cancelWithdrawal(id),
		onSuccess: invalidate,
	});
}

function usePayWithdrawalMutation() {
	const invalidate = useInvalidate([
		...MONEY_KEYS,
		OWNER_EARNINGS_QUERY_KEY,
		MY_COMMISSIONS_QUERY_KEY,
	]);
	return useMutation({
		mutationFn: ({
			id,
			...input
		}: {
			id: number;
			paid_cop_amount: string;
			cop_rate: string;
			payment_reference: string;
			note: string | null;
			receipt: ReceiptFile | null;
		}) => payWithdrawal(id, input),
		onSuccess: invalidate,
	});
}

function useAttachReceiptMutation() {
	const invalidate = useInvalidate([WITHDRAWALS_QUERY_KEY]);
	return useMutation({
		mutationFn: ({ id, receipt }: { id: number; receipt: ReceiptFile }) =>
			attachWithdrawalReceipt(id, receipt),
		onSuccess: invalidate,
	});
}

function useRejectWithdrawalMutation() {
	const invalidate = useInvalidate(MONEY_KEYS);
	return useMutation({
		mutationFn: ({ id, note }: { id: number; note: string }) =>
			rejectWithdrawal(id, note),
		onSuccess: invalidate,
	});
}

export {
	useAttachReceiptMutation,
	useCancelRedemptionMutation,
	useCancelWithdrawalMutation,
	useCreateFeeScheduleMutation,
	useCreatePayoutMethodMutation,
	useCreateWithdrawalMutation,
	useDeactivatePayoutMethodMutation,
	usePayWithdrawalMutation,
	useRejectWithdrawalMutation,
	useRequestRedemptionMutation,
	useSetCommissionSharesMutation,
};
