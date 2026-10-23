import type { RedemptionStatus } from '@/modules/fund/api/fund.api';
import type {
	PayoutKind,
	WithdrawalStatus,
} from '@/modules/fund/api/fund-payouts.api';
import { formatPercentValue } from '@/modules/shared/lib/format';

type BadgeVariant = 'default' | 'secondary' | 'outline' | 'destructive';

const WITHDRAWAL_STATUS_LABELS: Record<WithdrawalStatus, string> = {
	requested: 'Por pagar',
	paid: 'Pagado',
	rejected: 'Rechazado',
	canceled: 'Anulado',
};

const WITHDRAWAL_STATUS_BADGE_VARIANT: Record<WithdrawalStatus, BadgeVariant> =
	{
		requested: 'secondary',
		paid: 'default',
		rejected: 'destructive',
		canceled: 'outline',
	};

const WITHDRAWAL_STATUS_OPTIONS = (
	Object.keys(WITHDRAWAL_STATUS_LABELS) as WithdrawalStatus[]
).map((value) => ({ value, label: WITHDRAWAL_STATUS_LABELS[value] }));

const REDEMPTION_STATUS_LABELS: Record<RedemptionStatus, string> = {
	queued: 'Esperando la liquidación',
	applied: 'Aplicada',
	canceled: 'Anulada',
};

const PAYOUT_KIND_LABELS: Record<PayoutKind, string> = {
	bank: 'Cuenta bancaria',
	nequi: 'Nequi',
};

const PAYOUT_KIND_OPTIONS = (
	Object.keys(PAYOUT_KIND_LABELS) as PayoutKind[]
).map((value) => ({ value, label: PAYOUT_KIND_LABELS[value] }));

/** Etiquetas de los datos de un medio de pago (al pagar un retiro). */
const PAYOUT_DETAIL_LABELS: Record<string, string> = {
	holder_name: 'Titular',
	document_number: 'Documento',
	bank_name: 'Banco',
	account_type: 'Tipo de cuenta',
	account_number: 'Número de cuenta',
	phone: 'Celular',
};

/** `10 % de 0 % a 50 % de ganancia` (o `desde 100 % de ganancia`). */
function describeTier(fromPct: string, toPct: string | null, ratePct: string) {
	const range =
		toPct === null
			? `desde ${formatPercentValue(fromPct)} de ganancia`
			: `de ${formatPercentValue(fromPct)} a ${formatPercentValue(toPct)} de ganancia`;
	return `${formatPercentValue(ratePct)} ${range}`;
}

export {
	describeTier,
	PAYOUT_DETAIL_LABELS,
	PAYOUT_KIND_LABELS,
	PAYOUT_KIND_OPTIONS,
	REDEMPTION_STATUS_LABELS,
	WITHDRAWAL_STATUS_BADGE_VARIANT,
	WITHDRAWAL_STATUS_LABELS,
	WITHDRAWAL_STATUS_OPTIONS,
};
