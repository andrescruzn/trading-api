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

type PayoutKind = 'bank' | 'nequi';

type PayoutMethod = {
	id: number;
	user_id: number;
	kind: PayoutKind;
	label: string;
	/** Resumen sin datos completos: `Bancolombia · ahorros · ···6789`. */
	masked: string;
	/** Antes de esta fecha no recibe retiros (seguridad). */
	usable_from: string;
	is_active: boolean;
	created_at: string | null;
	/** Solo para un super admin al pagar un retiro. */
	details?: Record<string, string>;
};

type PayoutMethodInput = {
	kind: PayoutKind;
	label: string;
	holder_name: string;
	document_number: string;
	bank_name?: string;
	account_type?: string;
	account_number?: string;
	phone?: string;
};

type WithdrawalStatus = 'requested' | 'paid' | 'rejected' | 'canceled';

type Withdrawal = {
	id: number;
	user_id: number;
	amount: string;
	payout_method_id: number;
	status: WithdrawalStatus;
	paid_cop_amount: string | null;
	cop_rate: string | null;
	payment_reference: string | null;
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

function payWithdrawal(
	id: number,
	input: {
		paid_cop_amount: string;
		cop_rate: string;
		payment_reference: string;
		note: string | null;
		receipt: ReceiptFile | null;
	},
) {
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
	WithdrawalFilters,
	WithdrawalStatus,
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
	listMyCommissions,
	listMyPayoutMethods,
	listOwnerEarnings,
	listWithdrawals,
	payWithdrawal,
	rejectWithdrawal,
	requestRedemption,
	setCommissionShares,
};
