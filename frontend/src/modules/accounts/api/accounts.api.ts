import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// ======================================================================

type AccountMode = 'paper' | 'live';
type AccountStatus = 'active' | 'suspended';

type Account = {
	id: number;
	user_id: number;
	exchange_id: number | null;
	name: string;
	mode: AccountMode;
	base_currency: string;
	status: AccountStatus;
	credentials_ref: string | null;
	/** `true` si la cuenta tiene API key/secret cifradas guardadas. */
	has_credentials: boolean;
	meta: Record<string, unknown>;
	created_at: string | null;
	updated_at: string | null;
};

/** Saldos en string (DECIMAL del backend). */
type AccountBalance = {
	id: number;
	account_id: number;
	asset: string;
	free: string;
	locked: string;
	total: string;
	ts: string | null;
};

/**
 * Las credenciales solo se guardan si llegan API key y secret juntos; el
 * backend las cifra y nunca las devuelve.
 */
type AccountInput = {
	name: string;
	mode: AccountMode;
	base_currency: string;
	exchange_id: number | null;
	api_key?: string;
	api_secret?: string;
	credentials_label?: string;
};

/** El modo no se puede cambiar tras crear la cuenta; `exchange_id: null` se ignora. */
type AccountUpdate = {
	name?: string;
	status?: AccountStatus;
	base_currency?: string;
	exchange_id?: number;
	api_key?: string;
	api_secret?: string;
	credentials_label?: string;
};

/** Montos como string para no perder precisión (el backend los lee como Decimal). */
type BalanceInput = {
	asset: string;
	free: string;
	locked: string;
};

type BalanceFilters = {
	asset?: string;
	limit?: number;
};

// ======================================================================
// Cuentas
// ======================================================================

/** Usuario: sus cuentas. Admin: todas (incluye `user_id`). */
function listAccounts() {
	return api.get<Account[]>('/accounts');
}

function getAccount(id: number) {
	return api.get<Account>(`/accounts/${id}`);
}

function createAccount(input: AccountInput) {
	return api.post<Account>('/accounts', input);
}

function updateAccount(id: number, input: AccountUpdate) {
	return api.put<Account>(`/accounts/${id}`, input);
}

// ======================================================================
// Balances
// ======================================================================

/** El backend los devuelve del más reciente al más antiguo. */
function listBalances(accountId: number, filters: BalanceFilters = {}) {
	return api.get<AccountBalance[]>(`/accounts/${accountId}/balances`, filters);
}

function recordBalance(accountId: number, input: BalanceInput) {
	return api.post<AccountBalance>(`/accounts/${accountId}/balances`, input);
}

export type {
	Account,
	AccountBalance,
	AccountInput,
	AccountMode,
	AccountStatus,
	AccountUpdate,
	BalanceFilters,
	BalanceInput,
};
export {
	createAccount,
	getAccount,
	listAccounts,
	listBalances,
	recordBalance,
	updateAccount,
};
