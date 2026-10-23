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
type LedgerEntryType = 'deposit' | 'refund' | 'allocation';
type AllocationStatus = 'queued' | 'applied' | 'canceled';

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

// ----------------------------------------------------------------------
// Agentes del fondo (F4)
// ----------------------------------------------------------------------

/** Datos públicos del agente (sin cuenta ni credenciales). */
type FundAgentInfo = {
	bot_id: number;
	name: string;
	status: 'running' | 'stopped' | 'paused' | 'error';
	mode: 'paper' | 'live';
	symbol: string | null;
};

type FundPool = {
	id: number;
	bot_id: number;
	asset: string;
	/** Equity exacta de la última liquidación. */
	equity: string;
	units: string;
	/** Valor de una unidad en la última liquidación. */
	nav: string;
	/** Hoy: equity liquidada + resultado desde entonces (lo abierto a costo). */
	estimated_capital: string;
	queued_total: string;
	participants: number;
	last_settled_at: string | null;
	created_at: string | null;
	agent: FundAgentInfo | null;
};

type AllocationOrder = {
	id: number;
	pool_id: number;
	user_id: number;
	amount: string;
	source_bucket: LedgerBucket;
	status: AllocationStatus;
	note: string | null;
	settlement_id: number | null;
	created_by_user_id: number | null;
	created_at: string | null;
	resolved_at: string | null;
};

type AgentSettlement = {
	id: number;
	pool_id: number;
	previous_equity: string;
	/** Ventas − compras − comisiones desde la liquidación anterior. */
	trading_result: string;
	equity_before: string;
	units_before: string;
	nav: string;
	allocated_amount: string;
	units_issued: string;
	equity_after: string;
	units_after: string;
	fills_count: number;
	unvalued_fees: Record<string, string>;
	note: string | null;
	created_by_user_id: number | null;
	settled_at: string | null;
};

type PoolParticipant = {
	user_id: number;
	units: string;
	cost: string;
	value: string;
	/** Fracción 0–1 de las unidades del agente. */
	share: string;
	first_acquired_at: string | null;
};

type FundPoolDetail = FundPool & {
	participants_detail: PoolParticipant[];
	queued: AllocationOrder[];
	settlements: AgentSettlement[];
};

type SettlementPreview = {
	pool_id: number;
	/** Códigos que impiden liquidar ahora; `blocker_messages` es su texto. */
	blockers: string[];
	blocker_messages: string[];
	fills_count: number;
	sells: string;
	buys: string;
	fees: string;
	unvalued_fees: Record<string, string>;
	previous_equity: string;
	trading_result: string;
	equity_before: string;
	units_before: string;
	nav: string;
	allocations: (AllocationOrder & { units: string })[];
	canceled: (AllocationOrder & { reason: string })[];
	allocated_amount: string;
	units_issued: string;
	equity_after: string;
	units_after: string;
};

type Participation = {
	pool_id: number;
	agent: FundAgentInfo | null;
	units: string;
	cost: string;
	nav: string;
	/** Unidades × NAV de la última liquidación. */
	value: string;
	result: string;
	first_acquired_at: string | null;
	last_settled_at: string | null;
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

// ======================================================================
// Agentes del fondo (F4)
// ======================================================================

function listPools() {
	return api.get<FundPool[]>('/fund/agents');
}

function listEligibleAgents() {
	return api.get<FundAgentInfo[]>('/fund/agents/eligible');
}

function openPool(botId: number) {
	return api.post<FundPoolDetail>('/fund/agents', { bot_id: botId });
}

function getPool(poolId: number) {
	return api.get<FundPoolDetail>(`/fund/agents/${poolId}`);
}

function queueAllocation(
	poolId: number,
	input: { user_id: number; amount: string; source_bucket: LedgerBucket },
) {
	return api.post<AllocationOrder>(`/fund/agents/${poolId}/allocations`, input);
}

function cancelAllocation(orderId: number) {
	return api.post<AllocationOrder>(`/fund/allocations/${orderId}/cancel`);
}

function getSettlementPreview(poolId: number) {
	return api.get<SettlementPreview>(
		`/fund/agents/${poolId}/settlement-preview`,
	);
}

function settleAgent(poolId: number, note: string | null) {
	return api.post<AgentSettlement>(`/fund/agents/${poolId}/settle`, { note });
}

function listMyParticipations() {
	return api.get<Participation[]>('/fund/me/participations');
}

export type {
	AgentSettlement,
	AllocationOrder,
	AllocationStatus,
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
	FundAgentInfo,
	FundBalances,
	FundPool,
	FundPoolDetail,
	FundSettings,
	FundSettingsInput,
	LedgerBucket,
	LedgerEntry,
	LedgerEntryType,
	NetworkChoice,
	Participation,
	PoolParticipant,
	SettlementPreview,
	VerifySummary,
};
export {
	assignUnclaimedDeposit,
	cancelAllocation,
	cancelDeposit,
	confirmDeposit,
	createDeposit,
	getDepositInfo,
	getFundSettings,
	getMyBalances,
	getPool,
	getSettlementPreview,
	listAvailableNetworks,
	listDeposits,
	listEligibleAgents,
	listMyLedger,
	listMyParticipations,
	listParticipantBalances,
	listParticipantLedger,
	listPools,
	listUnclaimedDeposits,
	openPool,
	queueAllocation,
	refundPending,
	rejectDeposit,
	setDepositNetworks,
	settleAgent,
	updateFundSettings,
	verifyDeposits,
};
