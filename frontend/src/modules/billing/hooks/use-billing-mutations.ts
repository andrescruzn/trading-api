import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	type CloseBillingPeriodInput,
	closeBillingPeriod,
	createInvestor,
	createManagedAccount,
	type InvestorInput,
	type InvestorUpdate,
	type ManagedAccountInput,
	type ManagedAccountUpdate,
	type OpenBillingPeriodInput,
	openBillingPeriod,
	updateInvestor,
	updateManagedAccount,
} from '@/modules/billing/api/billing.api';
import {
	BILLING_PERIODS_QUERY_KEY,
	FEE_TRANSACTIONS_QUERY_KEY,
	INVESTORS_QUERY_KEY,
	MANAGED_ACCOUNTS_QUERY_KEY,
} from '@/modules/billing/hooks/use-billing-queries';

function useCreateInvestorMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: InvestorInput) => createInvestor(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: INVESTORS_QUERY_KEY }),
	});
}

function useUpdateInvestorMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({ id, input }: { id: number; input: InvestorUpdate }) =>
			updateInvestor(id, input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: INVESTORS_QUERY_KEY }),
	});
}

function useCreateManagedAccountMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: ManagedAccountInput) => createManagedAccount(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: MANAGED_ACCOUNTS_QUERY_KEY }),
	});
}

function useUpdateManagedAccountMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({ id, input }: { id: number; input: ManagedAccountUpdate }) =>
			updateManagedAccount(id, input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: MANAGED_ACCOUNTS_QUERY_KEY }),
	});
}

function useOpenBillingPeriodMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: OpenBillingPeriodInput) => openBillingPeriod(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: BILLING_PERIODS_QUERY_KEY }),
	});
}

function useCloseBillingPeriodMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({ id, input }: { id: number; input: CloseBillingPeriodInput }) =>
			closeBillingPeriod(id, input),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: BILLING_PERIODS_QUERY_KEY });
			// Cerrar puede crear una comisión pendiente y subir la marca de agua.
			queryClient.invalidateQueries({ queryKey: FEE_TRANSACTIONS_QUERY_KEY });
			queryClient.invalidateQueries({ queryKey: MANAGED_ACCOUNTS_QUERY_KEY });
		},
	});
}

export {
	useCloseBillingPeriodMutation,
	useCreateInvestorMutation,
	useCreateManagedAccountMutation,
	useOpenBillingPeriodMutation,
	useUpdateInvestorMutation,
	useUpdateManagedAccountMutation,
};
