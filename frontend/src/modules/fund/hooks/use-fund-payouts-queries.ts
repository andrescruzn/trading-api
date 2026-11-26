import { keepPreviousData, useQuery } from '@tanstack/react-query';
import {
	getCommissionShares,
	getFeeSchedule,
	getMyRedemptions,
	getMyWithdrawable,
	getWithdrawalPayoutDetails,
	getWithdrawNetworks,
	listMyCommissions,
	listMyPayoutMethods,
	listOwnerEarnings,
	listWithdrawals,
	type WithdrawalFilters,
} from '@/modules/fund/api/fund-payouts.api';
import type { PageParams } from '@/modules/shared/types/api';

const FEE_SCHEDULE_QUERY_KEY = ['fund-fee-schedule'] as const;
const COMMISSION_SHARES_QUERY_KEY = ['fund-commission-shares'] as const;
const OWNER_EARNINGS_QUERY_KEY = ['fund-owner-earnings'] as const;
const MY_COMMISSIONS_QUERY_KEY = ['fund-my-commissions'] as const;
const MY_REDEMPTIONS_QUERY_KEY = ['fund-my-redemptions'] as const;
const PAYOUT_METHODS_QUERY_KEY = ['fund-payout-methods'] as const;
const WITHDRAWABLE_QUERY_KEY = ['fund-withdrawable'] as const;
const WITHDRAWALS_QUERY_KEY = ['fund-withdrawals'] as const;
const PAYOUT_DETAILS_QUERY_KEY = ['fund-payout-details'] as const;
const WITHDRAW_NETWORKS_QUERY_KEY = ['fund-withdraw-networks'] as const;

const REFETCH_MS = 60_000;

function useFeeScheduleQuery() {
	return useQuery({
		queryKey: FEE_SCHEDULE_QUERY_KEY,
		queryFn: getFeeSchedule,
	});
}

function useCommissionSharesQuery() {
	return useQuery({
		queryKey: COMMISSION_SHARES_QUERY_KEY,
		queryFn: getCommissionShares,
	});
}

function useOwnerEarningsQuery() {
	return useQuery({
		queryKey: OWNER_EARNINGS_QUERY_KEY,
		queryFn: listOwnerEarnings,
	});
}

function useMyCommissionsQuery() {
	return useQuery({
		queryKey: MY_COMMISSIONS_QUERY_KEY,
		queryFn: listMyCommissions,
	});
}

function useMyRedemptionsQuery() {
	return useQuery({
		queryKey: MY_REDEMPTIONS_QUERY_KEY,
		queryFn: getMyRedemptions,
		refetchInterval: REFETCH_MS,
	});
}

function useMyPayoutMethodsQuery() {
	return useQuery({
		queryKey: PAYOUT_METHODS_QUERY_KEY,
		queryFn: listMyPayoutMethods,
	});
}

function useMyWithdrawableQuery() {
	return useQuery({
		queryKey: WITHDRAWABLE_QUERY_KEY,
		queryFn: getMyWithdrawable,
		refetchInterval: REFETCH_MS,
	});
}

function useWithdrawalsQuery(filters: WithdrawalFilters, page: PageParams) {
	return useQuery({
		queryKey: [...WITHDRAWALS_QUERY_KEY, filters, page],
		queryFn: () => listWithdrawals(filters, page),
		placeholderData: keepPreviousData,
		refetchInterval: REFETCH_MS,
	});
}

/** Redes de retiro con la comisión de Binance; cambian poco. */
function useWithdrawNetworksQuery(enabled = true) {
	return useQuery({
		queryKey: WITHDRAW_NETWORKS_QUERY_KEY,
		queryFn: getWithdrawNetworks,
		enabled,
		staleTime: 5 * 60_000,
	});
}

/** Dirección completa: solo al abrir el diálogo de enviar. */
function usePayoutDetailsQuery(withdrawalId: number | null) {
	return useQuery({
		queryKey: [...PAYOUT_DETAILS_QUERY_KEY, withdrawalId],
		queryFn: () => getWithdrawalPayoutDetails(withdrawalId as number),
		enabled: !!withdrawalId,
		// Datos sensibles: no se guardan en caché más de lo necesario
		gcTime: 0,
		staleTime: 0,
	});
}

export {
	COMMISSION_SHARES_QUERY_KEY,
	FEE_SCHEDULE_QUERY_KEY,
	MY_COMMISSIONS_QUERY_KEY,
	MY_REDEMPTIONS_QUERY_KEY,
	OWNER_EARNINGS_QUERY_KEY,
	PAYOUT_METHODS_QUERY_KEY,
	useCommissionSharesQuery,
	useFeeScheduleQuery,
	useMyCommissionsQuery,
	useMyPayoutMethodsQuery,
	useMyRedemptionsQuery,
	useMyWithdrawableQuery,
	useOwnerEarningsQuery,
	usePayoutDetailsQuery,
	useWithdrawalsQuery,
	useWithdrawNetworksQuery,
	WITHDRAWABLE_QUERY_KEY,
	WITHDRAWALS_QUERY_KEY,
};
