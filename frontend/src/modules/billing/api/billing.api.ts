import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// ======================================================================

type PeriodType = 'daily' | 'weekly' | 'monthly';
type BillingPeriodStatus = 'open' | 'closed';
type FeeTransactionStatus = 'pending' | 'charged' | 'waived';

/** `fee_pct` es una fracción en string (`0.2000` = 20 %). */
type Investor = {
	id: number;
	user_id: number;
	fee_pct: string;
	is_active: boolean;
	created_at: string | null;
	updated_at: string | null;
};

/** Montos en string (DECIMAL del backend). */
type ManagedAccount = {
	id: number;
	investor_id: number;
	account_id: number;
	bot_id: number | null;
	name: string;
	initial_capital: string;
	high_water_mark: string;
	period_type: PeriodType;
	is_active: boolean;
	created_at: string | null;
	updated_at: string | null;
};

/** Los campos de cierre son `null` mientras el período sigue abierto. */
type BillingPeriod = {
	id: number;
	managed_account_id: number;
	start_ts: string | null;
	end_ts: string | null;
	opening_equity: string;
	closing_equity: string | null;
	gross_pnl: string | null;
	/** Snapshot de la comisión del inversor al abrir el período (fracción). */
	fee_pct: string;
	fee_amount: string | null;
	net_pnl: string | null;
	status: BillingPeriodStatus;
	created_at: string | null;
	closed_at: string | null;
};

type FeeTransaction = {
	id: number;
	billing_period_id: number;
	managed_account_id: number;
	amount: string;
	status: FeeTransactionStatus;
	charged_at: string | null;
	notes: string | null;
	created_at: string | null;
};

type InvestorInput = { user_id: number; fee_pct: string };
type InvestorUpdate = { fee_pct?: string; is_active?: boolean };

type ManagedAccountInput = {
	investor_id: number;
	account_id: number;
	name: string;
	initial_capital: string;
	period_type: PeriodType;
	bot_id?: number | null;
};

/** `bot_id` sin enviar = no se cambia (el backend no permite quitarlo). */
type ManagedAccountUpdate = {
	name?: string;
	bot_id?: number;
	period_type?: PeriodType;
	is_active?: boolean;
};

type BillingFilters = {
	managed_account_id: number;
	limit?: number;
};

type OpenBillingPeriodInput = {
	managed_account_id: number;
	opening_equity: string;
};

type CloseBillingPeriodInput = { closing_equity: string };

// ======================================================================
// Inversores
// ======================================================================

/** Admin: todos. Inversor: solo su propio perfil. */
function listInvestors(filters: { only_active?: boolean } = {}) {
	return api.get<Investor[]>('/investors', filters);
}

function createInvestor(input: InvestorInput) {
	return api.post<Investor>('/investors', input);
}

function updateInvestor(id: number, input: InvestorUpdate) {
	return api.put<Investor>(`/investors/${id}`, input);
}

// ======================================================================
// Cuentas gestionadas
// ======================================================================

/** Admin: todas. Inversor: solo las suyas. */
function listManagedAccounts(filters: { only_active?: boolean } = {}) {
	return api.get<ManagedAccount[]>('/managed-accounts', filters);
}

function createManagedAccount(input: ManagedAccountInput) {
	return api.post<ManagedAccount>('/managed-accounts', input);
}

function updateManagedAccount(id: number, input: ManagedAccountUpdate) {
	return api.put<ManagedAccount>(`/managed-accounts/${id}`, input);
}

// ======================================================================
// Períodos de facturación y comisiones
// ======================================================================

function listBillingPeriods(filters: BillingFilters) {
	return api.get<BillingPeriod[]>('/billing-periods', filters);
}

function openBillingPeriod(input: OpenBillingPeriodInput) {
	return api.post<BillingPeriod>('/billing-periods/open', input);
}

/** Calcula la comisión de desempeño contra la marca de agua y cierra el período. */
function closeBillingPeriod(id: number, input: CloseBillingPeriodInput) {
	return api.post<BillingPeriod>(`/billing-periods/${id}/close`, input);
}

function listFeeTransactions(filters: BillingFilters) {
	return api.get<FeeTransaction[]>('/fee-transactions', filters);
}

export type {
	BillingFilters,
	BillingPeriod,
	BillingPeriodStatus,
	CloseBillingPeriodInput,
	FeeTransaction,
	FeeTransactionStatus,
	Investor,
	InvestorInput,
	InvestorUpdate,
	ManagedAccount,
	ManagedAccountInput,
	ManagedAccountUpdate,
	OpenBillingPeriodInput,
	PeriodType,
};
export {
	closeBillingPeriod,
	createInvestor,
	createManagedAccount,
	listBillingPeriods,
	listFeeTransactions,
	listInvestors,
	listManagedAccounts,
	openBillingPeriod,
	updateInvestor,
	updateManagedAccount,
};
