import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	setPlatformWallet,
	syncWallet,
} from '@/modules/accounts/api/wallet.api';
import { ACCOUNT_BALANCES_QUERY_KEY } from '@/modules/accounts/hooks/use-accounts-queries';
import {
	WALLET_QUERY_KEY,
	WALLET_SNAPSHOTS_QUERY_KEY,
} from '@/modules/accounts/hooks/use-wallet-queries';

function useInvalidateWallet() {
	const queryClient = useQueryClient();
	return () =>
		Promise.all([
			queryClient.invalidateQueries({ queryKey: WALLET_QUERY_KEY }),
			queryClient.invalidateQueries({ queryKey: WALLET_SNAPSHOTS_QUERY_KEY }),
		]);
}

function useSetPlatformWalletMutation() {
	const invalidate = useInvalidateWallet();
	return useMutation({
		mutationFn: (accountId: number) => setPlatformWallet(accountId),
		onSuccess: invalidate,
	});
}

function useSyncWalletMutation() {
	const queryClient = useQueryClient();
	const invalidate = useInvalidateWallet();
	return useMutation({
		mutationFn: syncWallet,
		// En live la sincronización también graba los balances de la cuenta.
		// En error también: el fallo queda guardado en la billetera.
		onSettled: () =>
			Promise.all([
				invalidate(),
				queryClient.invalidateQueries({ queryKey: ACCOUNT_BALANCES_QUERY_KEY }),
			]),
	});
}

export { useSetPlatformWalletMutation, useSyncWalletMutation };
