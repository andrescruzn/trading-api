import type { RedemptionStatus } from '@/modules/fund/api/fund.api';
import type {
	PayoutMethod,
	WithdrawalStatus,
} from '@/modules/fund/api/fund-payouts.api';
import { formatPercentValue } from '@/modules/shared/lib/format';

type BadgeVariant = 'default' | 'secondary' | 'outline' | 'destructive';

const WITHDRAWAL_STATUS_LABELS: Record<WithdrawalStatus, string> = {
	requested: 'Por enviar',
	paid: 'Enviado',
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

/** Etiquetas de los datos de una dirección de retiro (al enviar un retiro). */
const PAYOUT_DETAIL_LABELS: Record<string, string> = {
	network: 'Red',
	address: 'Dirección',
	memo: 'Memo',
};

/** Estado de un envío según Binance (al buscar el txid). */
const EXCHANGE_TX_STATUS_LABELS: Record<string, string> = {
	pending: 'En proceso',
	ok: 'Completado',
	failed: 'Fallido',
	canceled: 'Cancelado',
};

/**
 * Red de una dirección de retiro. La dirección va cifrada, así que la red se
 * lee del resumen (`TRC20 · TQ7xAb…9aBc`); las viejas de banco no tienen.
 */
function payoutNetwork(method: PayoutMethod | undefined): string | null {
	if (method?.kind !== 'crypto') return null;
	return method.masked.split(' · ')[0] || null;
}

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
	EXCHANGE_TX_STATUS_LABELS,
	PAYOUT_DETAIL_LABELS,
	payoutNetwork,
	REDEMPTION_STATUS_LABELS,
	WITHDRAWAL_STATUS_BADGE_VARIANT,
	WITHDRAWAL_STATUS_LABELS,
	WITHDRAWAL_STATUS_OPTIONS,
};
