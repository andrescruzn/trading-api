import type { Account } from '@/modules/accounts/api/accounts.api';
import type {
	BillingPeriod,
	BillingPeriodStatus,
	FeeTransactionStatus,
	Investor,
	ManagedAccount,
	PeriodType,
} from '@/modules/billing/api/billing.api';
import type { SelectOption } from '@/modules/shared/components/option-select';
import { toNumber } from '@/modules/shared/lib/format';

type BadgeVariant = 'default' | 'secondary' | 'outline' | 'destructive';

const PERIOD_TYPE_LABELS: Record<PeriodType, string> = {
	monthly: 'Mensual',
	weekly: 'Semanal',
	daily: 'Diario',
};

const PERIOD_TYPE_OPTIONS: SelectOption[] = Object.entries(
	PERIOD_TYPE_LABELS,
).map(([value, label]) => ({ value, label }));

const BILLING_PERIOD_STATUS_LABELS: Record<BillingPeriodStatus, string> = {
	open: 'Abierto',
	closed: 'Cerrado',
};

const BILLING_PERIOD_STATUS_VARIANTS: Record<
	BillingPeriodStatus,
	BadgeVariant
> = {
	open: 'default',
	closed: 'outline',
};

const FEE_STATUS_LABELS: Record<FeeTransactionStatus, string> = {
	pending: 'Pendiente',
	charged: 'Cobrada',
	waived: 'Exonerada',
};

const FEE_STATUS_VARIANTS: Record<FeeTransactionStatus, BadgeVariant> = {
	pending: 'outline',
	charged: 'secondary',
	waived: 'outline',
};

/** `20` → `'0.2000'`: el backend guarda la comisión como fracción con 4 decimales. */
function percentToFraction(percent: number): string {
	return (percent / 100).toFixed(4);
}

/** `'0.2000'` → `'20'`, para precargar un campo en %. */
function fractionToPercentText(fraction: string | null | undefined): string {
	const value = toNumber(fraction);
	return value === null ? '' : String(Number((value * 100).toFixed(2)));
}

/** Verde si hay ganancia, rojo si hay pérdida. */
function pnlClassName(
	value: string | number | null | undefined,
): string | undefined {
	const number = toNumber(value);
	if (number === null || number === 0) return undefined;
	return number > 0 ? 'text-chart-1' : 'text-destructive';
}

/** Suma un monto (string DECIMAL) de los períodos ya cerrados. */
function sumClosedPeriods(
	periods: BillingPeriod[] | undefined,
	key: 'net_pnl' | 'fee_amount' | 'gross_pnl',
): number {
	return (periods ?? [])
		.filter((period) => period.status === 'closed')
		.reduce((total, period) => total + (toNumber(period[key]) ?? 0), 0);
}

function investorLabel(investor: Investor): string {
	return `Inversor #${investor.id} · usuario #${investor.user_id}`;
}

function investorOptions(investors: Investor[] | undefined): SelectOption[] {
	return (investors ?? []).map((investor) => ({
		value: String(investor.id),
		label: investorLabel(investor),
	}));
}

function accountOptions(accounts: Account[] | undefined): SelectOption[] {
	return (accounts ?? []).map((account) => ({
		value: String(account.id),
		label: `${account.name} · ${account.mode === 'live' ? 'Live' : 'Paper'}`,
	}));
}

function managedAccountOptions(
	accounts: ManagedAccount[] | undefined,
): SelectOption[] {
	return (accounts ?? []).map((account) => ({
		value: String(account.id),
		label: account.is_active ? account.name : `${account.name} (inactiva)`,
	}));
}

export type { BadgeVariant };
export {
	accountOptions,
	BILLING_PERIOD_STATUS_LABELS,
	BILLING_PERIOD_STATUS_VARIANTS,
	FEE_STATUS_LABELS,
	FEE_STATUS_VARIANTS,
	fractionToPercentText,
	investorLabel,
	investorOptions,
	managedAccountOptions,
	PERIOD_TYPE_LABELS,
	PERIOD_TYPE_OPTIONS,
	percentToFraction,
	pnlClassName,
	sumClosedPeriods,
};
