import { keepPreviousData, useQuery } from '@tanstack/react-query';
import {
	type DepositFilters,
	getDepositInfo,
	getFundSettings,
	getMyBalances,
	listAvailableNetworks,
	listDeposits,
	listMyLedger,
	listParticipantBalances,
	listParticipantLedger,
	listUnclaimedDeposits,
} from '@/modules/fund/api/fund.api';
import type { PageParams } from '@/modules/shared/types/api';

const FUND_SETTINGS_QUERY_KEY = ['fund-settings'] as const;
const FUND_NETWORKS_QUERY_KEY = ['fund-available-networks'] as const;
const DEPOSIT_INFO_QUERY_KEY = ['fund-deposit-info'] as const;
const DEPOSITS_QUERY_KEY = ['fund-deposits'] as const;
const UNCLAIMED_QUERY_KEY = ['fund-unclaimed-deposits'] as const;
const MY_BALANCES_QUERY_KEY = ['fund-my-balances'] as const;
const LEDGER_QUERY_KEY = ['fund-ledger'] as const;
const PARTICIPANTS_QUERY_KEY = ['fund-participants'] as const;

// Los depósitos se confirman solos en el scheduler (cada pocos minutos):
// releer cada minuto muestra el cambio sin recargar.
const FUND_REFETCH_MS = 60_000;

function useFundSettingsQuery() {
	return useQuery({
		queryKey: FUND_SETTINGS_QUERY_KEY,
		queryFn: getFundSettings,
	});
}

/** Lee el exchange: solo cuando el diálogo de redes está abierto. */
function useAvailableNetworksQuery(enabled: boolean) {
	return useQuery({
		queryKey: FUND_NETWORKS_QUERY_KEY,
		queryFn: listAvailableNetworks,
		enabled,
		staleTime: 5 * 60_000,
	});
}

function useDepositInfoQuery() {
	return useQuery({
		queryKey: DEPOSIT_INFO_QUERY_KEY,
		queryFn: getDepositInfo,
	});
}

function useDepositsQuery(filters: DepositFilters, page: PageParams) {
	return useQuery({
		queryKey: [...DEPOSITS_QUERY_KEY, filters, page],
		queryFn: () => listDeposits(filters, page),
		placeholderData: keepPreviousData,
		refetchInterval: FUND_REFETCH_MS,
	});
}

/** Lee el exchange: solo cuando la pestaña está abierta. */
function useUnclaimedDepositsQuery(enabled: boolean) {
	return useQuery({
		queryKey: UNCLAIMED_QUERY_KEY,
		queryFn: listUnclaimedDeposits,
		enabled,
	});
}

function useMyBalancesQuery() {
	return useQuery({
		queryKey: MY_BALANCES_QUERY_KEY,
		queryFn: getMyBalances,
		refetchInterval: FUND_REFETCH_MS,
	});
}

/** `userId` null = mis movimientos; con id = los de esa persona (staff). */
function useLedgerQuery(
	userId: number | null,
	page: PageParams,
	enabled = true,
) {
	return useQuery({
		queryKey: [...LEDGER_QUERY_KEY, userId ?? 'me', page],
		queryFn: () =>
			userId === null
				? listMyLedger(page)
				: listParticipantLedger(userId, page),
		placeholderData: keepPreviousData,
		enabled,
	});
}

function useParticipantBalancesQuery() {
	return useQuery({
		queryKey: PARTICIPANTS_QUERY_KEY,
		queryFn: listParticipantBalances,
		refetchInterval: FUND_REFETCH_MS,
	});
}

export {
	DEPOSIT_INFO_QUERY_KEY,
	DEPOSITS_QUERY_KEY,
	FUND_NETWORKS_QUERY_KEY,
	FUND_SETTINGS_QUERY_KEY,
	LEDGER_QUERY_KEY,
	MY_BALANCES_QUERY_KEY,
	PARTICIPANTS_QUERY_KEY,
	UNCLAIMED_QUERY_KEY,
	useAvailableNetworksQuery,
	useDepositInfoQuery,
	useDepositsQuery,
	useFundSettingsQuery,
	useLedgerQuery,
	useMyBalancesQuery,
	useParticipantBalancesQuery,
	useUnclaimedDepositsQuery,
};
