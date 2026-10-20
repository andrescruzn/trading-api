import { keepPreviousData, useQuery } from '@tanstack/react-query';
import {
	getEquityEstimate,
	listBillingPeriods,
	listFeeTransactions,
	listInvestors,
	listManagedAccounts,
} from '@/modules/billing/api/billing.api';

const INVESTORS_QUERY_KEY = ['investors'] as const;
const MANAGED_ACCOUNTS_QUERY_KEY = ['managed-accounts'] as const;
const BILLING_PERIODS_QUERY_KEY = ['billing-periods'] as const;
const FEE_TRANSACTIONS_QUERY_KEY = ['fee-transactions'] as const;
const EQUITY_ESTIMATE_QUERY_KEY = ['equity-estimate'] as const;

function useInvestorsQuery(filters: { only_active?: boolean } = {}) {
	return useQuery({
		queryKey: [...INVESTORS_QUERY_KEY, filters],
		queryFn: () => listInvestors(filters),
	});
}

function useManagedAccountsQuery(filters: { only_active?: boolean } = {}) {
	return useQuery({
		queryKey: [...MANAGED_ACCOUNTS_QUERY_KEY, filters],
		queryFn: () => listManagedAccounts(filters),
	});
}

/** Solo consulta cuando hay una cuenta gestionada elegida. */
function useBillingPeriodsQuery(managedAccountId: number | null) {
	return useQuery({
		queryKey: [...BILLING_PERIODS_QUERY_KEY, managedAccountId],
		queryFn: () =>
			listBillingPeriods({ managed_account_id: managedAccountId as number }),
		enabled: !!managedAccountId,
		placeholderData: keepPreviousData,
	});
}

function useFeeTransactionsQuery(managedAccountId: number | null) {
	return useQuery({
		queryKey: [...FEE_TRANSACTIONS_QUERY_KEY, managedAccountId],
		queryFn: () =>
			listFeeTransactions({ managed_account_id: managedAccountId as number }),
		enabled: !!managedAccountId,
		placeholderData: keepPreviousData,
	});
}

/** Solo cuando se pide (diálogo abierto): lee balances y precios al momento. */
function useEquityEstimateQuery(
	managedAccountId: number | null,
	enabled: boolean,
) {
	return useQuery({
		queryKey: [...EQUITY_ESTIMATE_QUERY_KEY, managedAccountId],
		queryFn: () => getEquityEstimate(managedAccountId as number),
		enabled: enabled && !!managedAccountId,
		staleTime: 0,
	});
}

export {
	BILLING_PERIODS_QUERY_KEY,
	EQUITY_ESTIMATE_QUERY_KEY,
	FEE_TRANSACTIONS_QUERY_KEY,
	INVESTORS_QUERY_KEY,
	MANAGED_ACCOUNTS_QUERY_KEY,
	useBillingPeriodsQuery,
	useEquityEstimateQuery,
	useFeeTransactionsQuery,
	useInvestorsQuery,
	useManagedAccountsQuery,
};
