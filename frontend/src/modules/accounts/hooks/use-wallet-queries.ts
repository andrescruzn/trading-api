import { useQuery } from '@tanstack/react-query';
import {
	getWallet,
	listWalletSnapshots,
} from '@/modules/accounts/api/wallet.api';

const WALLET_QUERY_KEY = ['wallet'] as const;
const WALLET_SNAPSHOTS_QUERY_KEY = ['wallet-snapshots'] as const;

// El scheduler sincroniza cada pocos minutos: releer cada minuto basta para
// que la página muestre la foto nueva sin recargar.
const WALLET_REFETCH_MS = 60_000;

function useWalletQuery() {
	return useQuery({
		queryKey: WALLET_QUERY_KEY,
		queryFn: getWallet,
		refetchInterval: WALLET_REFETCH_MS,
	});
}

function useWalletSnapshotsQuery(limit = 20) {
	return useQuery({
		queryKey: [...WALLET_SNAPSHOTS_QUERY_KEY, limit],
		queryFn: () => listWalletSnapshots(limit),
		refetchInterval: WALLET_REFETCH_MS,
	});
}

export {
	useWalletQuery,
	useWalletSnapshotsQuery,
	WALLET_QUERY_KEY,
	WALLET_SNAPSHOTS_QUERY_KEY,
};
