import type { WalletSnapshotSource } from '@/modules/accounts/api/wallet.api';

/** De dónde salió una foto de saldo de la billetera. */
const WALLET_SOURCE_LABELS: Record<WalletSnapshotSource, string> = {
	exchange: 'Leído del exchange',
	manual: 'Registrado a mano',
};

export { WALLET_SOURCE_LABELS };
