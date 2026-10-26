import type {
	FundAgentInfo,
	RedemptionRequest,
	TierCharge,
} from '@/modules/fund/api/fund.api';
import type { ReceiptFile } from '@/modules/fund/api/fund-overview.api';
import { api } from '@/modules/shared/lib/api-client';
import type { PageParams, Paginated } from '@/modules/shared/types/api';

// ======================================================================
// Tipos (F5: comisión, salidas de los agentes y retiros). Porcentajes en %
// (20 = 20 %); montos como string (DECIMAL del backend).
// ======================================================================

type FeeTierPct = { from_return_pct: string; rate_pct: string };

type FeeSchedule = {
	id: number;
	tiers: FeeTierPct[];
	note: string | null;
	created_by_user_id: number | null;
	created_at: string | null;
};

type CommissionShares = {
	id: number;
	shares: { user_id: number; pct: string }[];
	note: string | null;
	created_by_user_id: number | null;
	created_at: string | null;
};

type OwnerEarning = { user_id: number; commissions: string };

type CommissionCredit = {
	id: number;
	settlement_redemption_id: number;
	amount: string;
	created_at: string | null;
};

/** Lo que salió de un agente para una persona, con su comisión. */
type SettlementRedemption = {
	id: number;
	settlement_id: number;
	redemption_request_id: number;
	pool_id: number;
	units: string;
	value: string;
	cost: string;
	gain: string;
	/** En % (200 = +200 %). */
	return_pct: string;
	fee: string;
	net: string;
	pending_amount: string | null;
	breakdown: TierCharge[];
	created_at: string | null;
};

type MyRedemptions = {
	queued: RedemptionRequest[];
	history: RedemptionRequest[];
	lines: SettlementRedemption[];
	/** `pool_id` → agente (también los de los que ya saliste del todo). */
	agents: Record<string, FundAgentInfo | null>;
};

/** `bank` / `nequi` solo en direcciones viejas (desactivadas): ya no se crean. */
type PayoutKind = 'crypto' | 'bank' | 'nequi';

type PayoutMethod = {
	id: number;
	user_id: number;
	kind: PayoutKind;
	label: string;
	/** Resumen sin la dirección completa: `TRC20 · TQ7xAb…9aBc`. */
	masked: string;
	/** Antes de esta fecha no recibe retiros (seguridad). */
	usable_from: string;
	is_active: boolean;
	created_at: string | null;
	/** Solo para un super admin al enviar un retiro: `network`, `address`, `memo`. */
	details?: Record<string, string>;
};

type PayoutMethodInput = {
	label: string;
	network: string;
	address: string;
	memo?: string;
};

/** Red por la que el fondo envía los retiros; comisión y mínimo de Binance (live). */
type WithdrawNetwork = {
	network: string;
	name: string;
	fee: string | null;
	min_amount: string | null;
	enabled: boolean;
};

type WithdrawNetworks = {
	asset: string;
	is_live: boolean;
	networks: WithdrawNetwork[];
};

/** Lo que dice Binance de un txid, comparado con el retiro (antes de registrarlo). */
type WithdrawalCheck = {
	txid: string;
	is_live: boolean;
	found: boolean;
	/** `pending` | `ok` | `failed` | `canceled` */
	status: string | null;
	sent_amount: string | null;
	network_fee: string | null;
	network: string | null;
	address: string | null;
	/** `null` = no se pudo comparar. */
	address_matches: boolean | null;
	amount_matches: boolean | null;
	/** Binance no respondió (se registra con nota). */
	exchange_error: string | null;
	explorer_url: string | null;
};

type WithdrawalStatus = 'requested' | 'paid' | 'rejected' | 'canceled';

type Withdrawal = {
	id: number;
	user_id: number;
	amount: string;
	payout_method_id: number;
	status: WithdrawalStatus;
	/** Datos del envío (al pagarlo). */
	txid: string | null;
	network: string | null;
	sent_amount: string | null;
	network_fee: string | null;
	explorer_url: string | null;
	resolution_note: string | null;
	resolved_by_user_id: number | null;
	resolved_at: string | null;
	created_at: string | null;
	/** Nombre del comprobante del pago, si tiene (F6). */
	receipt_name: string | null;
};

type WithdrawalFilters = { status?: WithdrawalStatus; user_id?: number };

// ======================================================================
// Comisión
// ======================================================================

/**
 * Sin tabla publicada el backend responde `data: []` (el envelope nunca manda
 * `null`): se normaliza a `null` para que `if (schedule)` no lo tome como tabla.
 */
async function getFeeSchedule(): Promise<FeeSchedule | null> {
	const schedule = await api.get<FeeSchedule | []>('/fund/fees');
	return Array.isArray(schedule) ? null : schedule;
}

function createFeeSchedule(input: {
	tiers: FeeTierPct[];
	note: string | null;
}) {
	return api.post<FeeSchedule>('/fund/fees', input);
}

function getCommissionShares() {
	return api.get<{
		current: CommissionShares | null;
		history: CommissionShares[];
	}>('/fund/commission-shares');
}

function setCommissionShares(input: {
	shares: { user_id: number; pct: string }[];
	note: string | null;
}) {
	return api.put<CommissionShares>('/fund/commission-shares', input);
}

function listOwnerEarnings() {
	return api.get<OwnerEarning[]>('/fund/commissions');
}

function listMyCommissions() {
	return api.get<CommissionCredit[]>('/fund/me/commissions');
}

// ======================================================================
// Salidas de los agentes
// ======================================================================

function requestRedemption(input: {
	pool_id: number;
	amount: string | null;
	user_id?: number;
}) {
	return api.post<RedemptionRequest>('/fund/redemptions', input);
}

function cancelRedemption(id: number) {
	return api.post<RedemptionRequest>(`/fund/redemptions/${id}/cancel`);
}

function getMyRedemptions() {
	return api.get<MyRedemptions>('/fund/me/redemptions');
}

// ======================================================================
// Medios de pago y retiros
// ======================================================================

function getWithdrawNetworks() {
	return api.get<WithdrawNetworks>('/fund/withdrawals/networks');
}

function listMyPayoutMethods() {
	return api.get<PayoutMethod[]>('/fund/me/payout-methods');
}

function createPayoutMethod(input: PayoutMethodInput) {
	return api.post<PayoutMethod>('/fund/me/payout-methods', input);
}

function deactivatePayoutMethod(id: number) {
	return api.post<null>(`/fund/me/payout-methods/${id}/deactivate`);
}

function getMyWithdrawable() {
	return api.get<{ withdrawable: string }>('/fund/me/withdrawable');
}

function createWithdrawal(input: { amount: string; payout_method_id: number }) {
	return api.post<Withdrawal>('/fund/withdrawals', input);
}

function listWithdrawals(filters: WithdrawalFilters, page: PageParams) {
	return api.get<Paginated<Withdrawal>>('/fund/withdrawals', {
		...filters,
		...page,
	});
}

function cancelWithdrawal(id: number) {
	return api.post<Withdrawal>(`/fund/withdrawals/${id}/cancel`);
}

function getWithdrawalPayoutDetails(id: number) {
	return api.get<PayoutMethod>(`/fund/withdrawals/${id}/payout-details`);
}

function lookupWithdrawal(id: number, txid: string) {
	return api.post<WithdrawalCheck>(`/fund/withdrawals/${id}/lookup`, { txid });
}

/** `sent_amount` / `network_fee` solo si Binance no muestra el envío. */
type WithdrawalPayInput = {
	txid: string;
	sent_amount: string | null;
	network_fee: string | null;
	note: string | null;
	receipt: ReceiptFile | null;
};

function payWithdrawal(id: number, input: WithdrawalPayInput) {
	return api.post<Withdrawal>(`/fund/withdrawals/${id}/pay`, input);
}

function attachWithdrawalReceipt(id: number, receipt: ReceiptFile) {
	return api.put<Withdrawal>(`/fund/withdrawals/${id}/receipt`, receipt);
}

function rejectWithdrawal(id: number, note: string) {
	return api.post<Withdrawal>(`/fund/withdrawals/${id}/reject`, { note });
}

export type {
	CommissionCredit,
	CommissionShares,
	FeeSchedule,
	FeeTierPct,
	MyRedemptions,
	OwnerEarning,
	PayoutKind,
	PayoutMethod,
	PayoutMethodInput,
	SettlementRedemption,
	Withdrawal,
	WithdrawalCheck,
	WithdrawalFilters,
	WithdrawalPayInput,
	WithdrawalStatus,
	WithdrawNetwork,
	WithdrawNetworks,
};
export {
	attachWithdrawalReceipt,
	cancelRedemption,
	cancelWithdrawal,
	createFeeSchedule,
	createPayoutMethod,
	createWithdrawal,
	deactivatePayoutMethod,
	getCommissionShares,
	getFeeSchedule,
	getMyRedemptions,
	getMyWithdrawable,
	getWithdrawalPayoutDetails,
	getWithdrawNetworks,
	listMyCommissions,
	listMyPayoutMethods,
	listOwnerEarnings,
	listWithdrawals,
	lookupWithdrawal,
	payWithdrawal,
	rejectWithdrawal,
	requestRedemption,
	setCommissionShares,
};
