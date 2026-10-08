import { keepPreviousData, useQuery } from '@tanstack/react-query';
import {
	type BalanceFilters,
	getAccount,
	listAccounts,
	listBalances,
} from '@/modules/accounts/api/accounts.api';

const ACCOUNTS_QUERY_KEY = ['accounts'] as const;
const ACCOUNT_BALANCES_QUERY_KEY = ['account-balances'] as const;

function useAccountsQuery() {
	return useQuery({
		queryKey: ACCOUNTS_QUERY_KEY,
		queryFn: listAccounts,
	});
}

function useAccountQuery(id: number | null) {
	return useQuery({
		queryKey: [...ACCOUNTS_QUERY_KEY, id],
		queryFn: () => getAccount(id as number),
		enabled: !!id,
	});
}

/** Solo consulta cuando hay una cuenta elegida. */
function useAccountBalancesQuery(
	accountId: number | null,
	filters: BalanceFilters = {},
) {
	return useQuery({
		queryKey: [...ACCOUNT_BALANCES_QUERY_KEY, accountId, filters],
		queryFn: () => listBalances(accountId as number, filters),
		enabled: !!accountId,
		placeholderData: keepPreviousData,
	});
}

export {
	ACCOUNT_BALANCES_QUERY_KEY,
	ACCOUNTS_QUERY_KEY,
	useAccountBalancesQuery,
	useAccountQuery,
	useAccountsQuery,
};
