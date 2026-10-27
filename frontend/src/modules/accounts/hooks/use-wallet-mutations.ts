import { useMutation, useQueryClient } from '@tanstack/react-query';
import { syncWallet } from '@/modules/accounts/api/wallet.api';
import {
	WALLET_QUERY_KEY,
	WALLET_SNAPSHOTS_QUERY_KEY,
} from '@/modules/accounts/hooks/use-wallet-queries';

function useSyncWalletMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: syncWallet,
		// En error también: el fallo queda guardado en la billetera.
		onSettled: () =>
			Promise.all([
				queryClient.invalidateQueries({ queryKey: WALLET_QUERY_KEY }),
				queryClient.invalidateQueries({ queryKey: WALLET_SNAPSHOTS_QUERY_KEY }),
			]),
	});
}

export { useSyncWalletMutation };
