import type {
	Account,
	AccountMode,
	AccountStatus,
} from '@/modules/accounts/api/accounts.api';
import type { SelectOption } from '@/modules/shared/components/option-select';

type BadgeVariant = 'default' | 'secondary' | 'outline' | 'destructive';

const ACCOUNT_MODE_LABELS: Record<AccountMode, string> = {
	paper: 'Paper',
	live: 'Live',
};

const ACCOUNT_STATUS_LABELS: Record<AccountStatus, string> = {
	active: 'Activa',
	suspended: 'Suspendida',
};

/** Live opera con dinero real: se resalta en rojo para que nunca pase desapercibida. */
const ACCOUNT_MODE_BADGE_VARIANT: Record<AccountMode, BadgeVariant> = {
	paper: 'secondary',
	live: 'destructive',
};

const ACCOUNT_STATUS_BADGE_VARIANT: Record<AccountStatus, BadgeVariant> = {
	active: 'secondary',
	suspended: 'outline',
};

/** En el formulario se explica el modo, no solo se nombra. */
const ACCOUNT_MODE_OPTIONS: SelectOption[] = [
	{ value: 'paper', label: 'Paper (simulado, sin dinero real)' },
	{ value: 'live', label: 'Live (dinero real)' },
];

const ACCOUNT_STATUS_OPTIONS: SelectOption[] = Object.entries(
	ACCOUNT_STATUS_LABELS,
).map(([value, label]) => ({ value, label }));

/** `Mi cuenta Binance · Paper`. */
function accountOptions(accounts: Account[] | undefined): SelectOption[] {
	return (accounts ?? []).map((account) => ({
		value: String(account.id),
		label: `${account.name} · ${ACCOUNT_MODE_LABELS[account.mode] ?? account.mode}`,
	}));
}

export {
	ACCOUNT_MODE_BADGE_VARIANT,
	ACCOUNT_MODE_LABELS,
	ACCOUNT_MODE_OPTIONS,
	ACCOUNT_STATUS_BADGE_VARIANT,
	ACCOUNT_STATUS_LABELS,
	ACCOUNT_STATUS_OPTIONS,
	accountOptions,
};
