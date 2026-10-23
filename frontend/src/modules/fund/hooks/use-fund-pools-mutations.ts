import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	cancelAllocation,
	type LedgerBucket,
	openPool,
	queueAllocation,
	settleAgent,
} from '@/modules/fund/api/fund.api';
import {
	FUND_OVERVIEW_QUERY_KEY,
	MY_SUMMARY_QUERY_KEY,
} from '@/modules/fund/hooks/use-fund-overview-queries';
import {
	ELIGIBLE_AGENTS_QUERY_KEY,
	PARTICIPATIONS_QUERY_KEY,
	POOLS_QUERY_KEY,
	SETTLEMENT_PREVIEW_QUERY_KEY,
} from '@/modules/fund/hooks/use-fund-pools-queries';
import {
	LEDGER_QUERY_KEY,
	MY_BALANCES_QUERY_KEY,
	PARTICIPANTS_QUERY_KEY,
} from '@/modules/fund/hooks/use-fund-queries';

/** Lo que cambia al mover dinero hacia los agentes. */
function useInvalidatePools() {
	const queryClient = useQueryClient();
	return () =>
		Promise.all(
			[
				POOLS_QUERY_KEY,
				ELIGIBLE_AGENTS_QUERY_KEY,
				SETTLEMENT_PREVIEW_QUERY_KEY,
				PARTICIPATIONS_QUERY_KEY,
				LEDGER_QUERY_KEY,
				MY_BALANCES_QUERY_KEY,
				PARTICIPANTS_QUERY_KEY,
				FUND_OVERVIEW_QUERY_KEY,
				MY_SUMMARY_QUERY_KEY,
			].map((queryKey) => queryClient.invalidateQueries({ queryKey })),
		);
}

function useOpenPoolMutation() {
	const invalidate = useInvalidatePools();
	return useMutation({
		mutationFn: (botId: number) => openPool(botId),
		onSuccess: invalidate,
	});
}

function useQueueAllocationMutation() {
	const invalidate = useInvalidatePools();
	return useMutation({
		mutationFn: ({
			poolId,
			userId,
			amount,
			sourceBucket,
		}: {
			poolId: number;
			userId: number;
			amount: string;
			sourceBucket: LedgerBucket;
		}) =>
			queueAllocation(poolId, {
				user_id: userId,
				amount,
				source_bucket: sourceBucket,
			}),
		onSuccess: invalidate,
	});
}

function useCancelAllocationMutation() {
	const invalidate = useInvalidatePools();
	return useMutation({
		mutationFn: (orderId: number) => cancelAllocation(orderId),
		onSuccess: invalidate,
	});
}

function useSettleAgentMutation() {
	const invalidate = useInvalidatePools();
	return useMutation({
		mutationFn: ({ poolId, note }: { poolId: number; note: string | null }) =>
			settleAgent(poolId, note),
		onSuccess: invalidate,
	});
}

export {
	useCancelAllocationMutation,
	useOpenPoolMutation,
	useQueueAllocationMutation,
	useSettleAgentMutation,
};
