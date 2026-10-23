import type {
	AllocationStatus,
	DepositReviewReason,
	DepositStatus,
	LedgerBucket,
	LedgerEntryType,
} from '@/modules/fund/api/fund.api';

type BadgeVariant = 'default' | 'secondary' | 'outline' | 'destructive';

const DEPOSIT_STATUS_LABELS: Record<DepositStatus, string> = {
	pending: 'Esperando al exchange',
	review: 'En revisión',
	confirmed: 'Confirmado',
	rejected: 'Rechazado',
	expired: 'Vencido',
	canceled: 'Anulado',
};

const DEPOSIT_STATUS_BADGE_VARIANT: Record<DepositStatus, BadgeVariant> = {
	pending: 'secondary',
	review: 'outline',
	confirmed: 'default',
	rejected: 'destructive',
	expired: 'outline',
	canceled: 'outline',
};

const DEPOSIT_STATUS_OPTIONS = (
	Object.keys(DEPOSIT_STATUS_LABELS) as DepositStatus[]
).map((value) => ({ value, label: DEPOSIT_STATUS_LABELS[value] }));

/** Por qué un depósito espera a un super admin (lo ve también quien depositó). */
const DEPOSIT_REVIEW_REASON_LABELS: Record<DepositReviewReason, string> = {
	amount_mismatch: 'El monto que llegó no coincide con el declarado',
	over_threshold: 'Supera el tope de confirmación automática',
	exchange_failed: 'El exchange lo marcó como fallido o cancelado',
	wrong_asset: 'Llegó en otra moneda',
};

const LEDGER_ENTRY_TYPE_LABELS: Record<LedgerEntryType, string> = {
	deposit: 'Depósito',
	refund: 'Devolución',
	allocation: 'Asignación a un agente',
};

const LEDGER_BUCKET_LABELS: Record<LedgerBucket, string> = {
	pending: 'Pendiente de asignar',
	available: 'Disponible',
};

const ALLOCATION_SOURCE_OPTIONS = (
	Object.keys(LEDGER_BUCKET_LABELS) as LedgerBucket[]
).map((value) => ({ value, label: LEDGER_BUCKET_LABELS[value] }));

const ALLOCATION_STATUS_LABELS: Record<AllocationStatus, string> = {
	queued: 'En cola',
	applied: 'Aplicada',
	canceled: 'Cancelada',
};

export {
	ALLOCATION_SOURCE_OPTIONS,
	ALLOCATION_STATUS_LABELS,
	DEPOSIT_REVIEW_REASON_LABELS,
	DEPOSIT_STATUS_BADGE_VARIANT,
	DEPOSIT_STATUS_LABELS,
	DEPOSIT_STATUS_OPTIONS,
	LEDGER_BUCKET_LABELS,
	LEDGER_ENTRY_TYPE_LABELS,
};
