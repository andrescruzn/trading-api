import { api } from '@/modules/shared/lib/api-client';
import type { PageParams, Paginated } from '@/modules/shared/types/api';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// Fondo común: ajustes, depósitos verificados y libro mayor. Los montos
// llegan como string (DECIMAL del backend).
// ======================================================================

type DepositStatus =
	| 'pending'
	| 'review'
	| 'confirmed'
	| 'rejected'
	| 'expired'
	| 'canceled';

type DepositReviewReason =
	| 'amount_mismatch'
	| 'over_threshold'
	| 'exchange_failed'
	| 'wrong_asset';

type LedgerBucket = 'pending' | 'available';
type LedgerEntryType = 'deposit' | 'refund';

type DepositNetworkConfig = {
	network: string;
	name: string;
	address: string;
	/** Memo que exigen algunas redes; `null` si no aplica. */
	tag: string | null;
};

type FundSettings = {
	min_hold_days: number;
	deposit_auto_confirm_max: string;
	deposit_request_ttl_hours: number;
	deposit_networks: DepositNetworkConfig[];
	updated_by_user_id: number | null;
	updated_at: string | null;
};

type FundSettingsInput = {
	min_hold_days: number;
	deposit_auto_confirm_max: string;
	deposit_request_ttl_hours: number;
};

type AvailableNetwork = {
	code: string;
	name: string;
	deposit_enabled: boolean;
};

type AvailableNetworks = {
	asset: string;
	/** `false` = billetera de práctica: las direcciones se escriben a mano. */
	is_live: boolean;
	networks: AvailableNetwork[];
};

type NetworkChoice = {
	network: string;
	name?: string | null;
	/** Solo con billetera de práctica. */
	address?: string | null;
	tag?: string | null;
};

type DepositInfo = {
	/** `false` = aún no se puede depositar (sin billetera o sin redes). */
	enabled: boolean;
	asset: string | null;
	networks: DepositNetworkConfig[];
	min_hold_days: number;
	request_ttl_hours: number;
};

type DepositRequest = {
	id: number;
	user_id: number;
	asset: string;
	network: string;
	txid: string;
	declared_amount: string;
	/** Lo que reportó el exchange (lo que se acredita). */
	credited_amount: string | null;
	address_from: string | null;
	exchange_status: string | null;
	status: DepositStatus;
	review_reason: DepositReviewReason | null;
	resolved_by_user_id: number | null;
	resolved_at: string | null;
	resolution_note: string | null;
	expires_at: string | null;
	created_at: string | null;
};

type DepositInput = {
	network: string;
	txid: string;
	amount: string;
};

type DepositFilters = {
	status?: DepositStatus;
	/** Solo staff. */
	user_id?: number;
};

type ExchangeDeposit = {
	txid: string;
	amount: string;
	asset: string;
	network: string | null;
	status: string;
	address_from: string | null;
	ts: string | null;
};

type VerifySummary = {
	checked: number;
	confirmed: number;
	review: number;
	expired: number;
	waiting: number;
};

type FundBalances = {
	user_id: number;
	/** Pendiente de asignar: aún no pasó por un agente, no se retira. */
	pending: string;
	/** Disponible: se puede retirar. */
	available: string;
	total: string;
};

type LedgerEntry = {
	id: number;
	user_id: number;
	entry_type: LedgerEntryType;
	bucket: LedgerBucket;
	/** Con signo: + entra, − sale. */
	amount: string;
	asset: string;
	ref_type: string | null;
	ref_id: number | null;
	bot_id: number | null;
	description: string | null;
	created_by_user_id: number | null;
	created_at: string | null;
};

// ======================================================================
// Ajustes
// ======================================================================

function getFundSettings() {
	return api.get<FundSettings>('/fund/settings');
}

function updateFundSettings(input: FundSettingsInput) {
	return api.put<FundSettings>('/fund/settings', input);
}

function listAvailableNetworks() {
	return api.get<AvailableNetworks>('/fund/settings/networks/available');
}

function setDepositNetworks(networks: NetworkChoice[]) {
	return api.put<FundSettings>('/fund/settings/networks', { networks });
}

// ======================================================================
// Depósitos
// ======================================================================

function getDepositInfo() {
	return api.get<DepositInfo>('/fund/deposits/info');
}

function createDeposit(input: DepositInput) {
	return api.post<DepositRequest>('/fund/deposits', input);
}

function listDeposits(filters: DepositFilters, page: PageParams) {
	return api.get<Paginated<DepositRequest>>('/fund/deposits', {
		...filters,
		...page,
	});
}

function cancelDeposit(id: number) {
	return api.post<DepositRequest>(`/fund/deposits/${id}/cancel`);
}

function confirmDeposit(
	id: number,
	input: { amount?: string | null; note?: string | null },
) {
	return api.post<DepositRequest>(`/fund/deposits/${id}/confirm`, input);
}

function rejectDeposit(id: number, note: string) {
	return api.post<DepositRequest>(`/fund/deposits/${id}/reject`, { note });
}

function verifyDeposits() {
	return api.post<VerifySummary>('/fund/deposits/verify');
}

function listUnclaimedDeposits() {
	return api.get<ExchangeDeposit[]>('/fund/deposits/unclaimed');
}

function assignUnclaimedDeposit(input: {
	txid: string;
	user_id: number;
	note: string;
}) {
	return api.post<DepositRequest>('/fund/deposits/unclaimed/assign', input);
}

// ======================================================================
// Libro mayor
// ======================================================================

function getMyBalances() {
	return api.get<FundBalances>('/fund/me/balances');
}

function listMyLedger(page: PageParams) {
	return api.get<Paginated<LedgerEntry>>('/fund/me/ledger', page);
}

function listParticipantBalances() {
	return api.get<FundBalances[]>('/fund/participants');
}

function listParticipantLedger(userId: number, page: PageParams) {
	return api.get<Paginated<LedgerEntry>>(
		`/fund/participants/${userId}/ledger`,
		page,
	);
}

function refundPending(
	userId: number,
	input: { amount: string; reason: string },
) {
	return api.post<LedgerEntry>(`/fund/participants/${userId}/refunds`, input);
}

export type {
	AvailableNetwork,
	AvailableNetworks,
	DepositFilters,
	DepositInfo,
	DepositInput,
	DepositNetworkConfig,
	DepositRequest,
	DepositReviewReason,
	DepositStatus,
	ExchangeDeposit,
	FundBalances,
	FundSettings,
	FundSettingsInput,
	LedgerBucket,
	LedgerEntry,
	LedgerEntryType,
	NetworkChoice,
	VerifySummary,
};
export {
	assignUnclaimedDeposit,
	cancelDeposit,
	confirmDeposit,
	createDeposit,
	getDepositInfo,
	getFundSettings,
	getMyBalances,
	listAvailableNetworks,
	listDeposits,
	listMyLedger,
	listParticipantBalances,
	listParticipantLedger,
	listUnclaimedDeposits,
	refundPending,
	rejectDeposit,
	setDepositNetworks,
	updateFundSettings,
	verifyDeposits,
};
