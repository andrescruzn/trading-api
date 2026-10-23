import type {
	AccountMode,
	AccountStatus,
} from '@/modules/accounts/api/accounts.api';
import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// Billetera de la plataforma: la única cuenta de exchange del fondo común.
// Solo la ven super admin y socio; el inversor nunca ve su saldo total.
// ======================================================================

type WalletSnapshotSource = 'exchange' | 'manual';

/** Montos en string (DECIMAL del backend), valorados en `base_asset`. */
type WalletAssetLine = {
	asset: string;
	free: string;
	locked: string;
	total: string;
	/** `null` = sin precio: no suma al total. */
	price: string | null;
	value: string | null;
};

type WalletSnapshot = {
	id: number;
	account_id: number;
	base_asset: string;
	total_value: string;
	free_value: string;
	locked_value: string;
	source: WalletSnapshotSource;
	missing_prices: string[];
	assets: WalletAssetLine[];
	ts: string | null;
};

type PlatformWallet = {
	account_id: number;
	base_asset: string;
	last_synced_at: string | null;
	last_sync_error: string | null;
	/** Texto de UI del último fallo (ya en español). */
	last_sync_error_msg: string | null;
	updated_by_user_id: number | null;
	updated_at: string | null;
};

type WalletAccount = {
	id: number;
	name: string;
	mode: AccountMode;
	status: AccountStatus;
	exchange_id: number | null;
};

type WalletOverview = {
	configured: boolean;
	wallet: PlatformWallet | null;
	account: WalletAccount | null;
	latest_snapshot: WalletSnapshot | null;
};

// ======================================================================
// Llamadas
// ======================================================================

function getWallet() {
	return api.get<WalletOverview>('/wallet');
}

/** Solo super admin. */
function setPlatformWallet(accountId: number) {
	return api.put<WalletOverview>('/wallet', { account_id: accountId });
}

/** Solo super admin: lee el saldo del exchange ahora. */
function syncWallet() {
	return api.post<WalletOverview>('/wallet/sync');
}

function listWalletSnapshots(limit = 50) {
	return api.get<WalletSnapshot[]>('/wallet/snapshots', { limit });
}

export type {
	PlatformWallet,
	WalletAccount,
	WalletAssetLine,
	WalletOverview,
	WalletSnapshot,
	WalletSnapshotSource,
};
export { getWallet, listWalletSnapshots, setPlatformWallet, syncWallet };
