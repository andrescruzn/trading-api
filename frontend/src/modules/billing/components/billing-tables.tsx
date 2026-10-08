import type { ReactNode } from 'react';
import type {
	BillingPeriod,
	FeeTransaction,
} from '@/modules/billing/api/billing.api';
import {
	BILLING_PERIOD_STATUS_LABELS,
	BILLING_PERIOD_STATUS_VARIANTS,
	FEE_STATUS_LABELS,
	FEE_STATUS_VARIANTS,
	pnlClassName,
} from '@/modules/billing/lib/billing-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { formatDate, formatPercent, formatPrice } from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import { cn } from '@/modules/ui/lib/utils';

const MONEY = 'text-right font-mono tabular-nums';

type ListState<T> = {
	rows: T[] | undefined;
	isLoading: boolean;
	error: unknown;
	empty: ReactNode;
};

type BillingPeriodsTableProps = ListState<BillingPeriod> & {
	/** Columna extra al final (p. ej. el botón "Cerrar" del admin). */
	renderActions?: (period: BillingPeriod) => ReactNode;
};

export function BillingPeriodsTable({
	rows,
	isLoading,
	error,
	empty,
	renderActions,
}: BillingPeriodsTableProps) {
	const columns: DataTableColumn<BillingPeriod>[] = [
		{ id: 'id', header: 'Período', className: 'w-20 font-mono', cell: (row) => `#${row.id}` },
		{ id: 'start', header: 'Inicio', cell: (row) => formatDate(row.start_ts) },
		{ id: 'end', header: 'Cierre', cell: (row) => formatDate(row.end_ts) },
		{
			id: 'opening',
			header: 'Equity apertura',
			className: MONEY,
			cell: (row) => formatPrice(row.opening_equity),
		},
		{
			id: 'closing',
			header: 'Equity cierre',
			className: MONEY,
			cell: (row) => formatPrice(row.closing_equity),
		},
		{
			id: 'gross',
			header: 'PnL bruto',
			className: MONEY,
			cell: (row) => (
				<span className={pnlClassName(row.gross_pnl)}>{formatPrice(row.gross_pnl)}</span>
			),
		},
		{
			id: 'fee_pct',
			header: 'Comisión %',
			className: MONEY,
			cell: (row) => formatPercent(row.fee_pct),
		},
		{
			id: 'fee',
			header: 'Comisión',
			className: MONEY,
			cell: (row) => formatPrice(row.fee_amount),
		},
		{
			id: 'net',
			header: 'PnL neto',
			className: MONEY,
			cell: (row) => (
				<span className={pnlClassName(row.net_pnl)}>{formatPrice(row.net_pnl)}</span>
			),
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => (
				<Badge variant={BILLING_PERIOD_STATUS_VARIANTS[row.status] ?? 'outline'}>
					{BILLING_PERIOD_STATUS_LABELS[row.status] ?? row.status}
				</Badge>
			),
		},
	];

	if (renderActions) {
		columns.push({
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: renderActions,
		});
	}

	return (
		<DataTable
			columns={columns}
			rows={rows}
			getRowId={(row) => row.id}
			isLoading={isLoading}
			error={error}
			errorTitle="No pudimos cargar los períodos de facturación"
			empty={empty}
		/>
	);
}

type FeeTransactionsTableProps = ListState<FeeTransaction> & {
	/** Las notas son internas: solo las ve el administrador. */
	showNotes?: boolean;
};

export function FeeTransactionsTable({
	rows,
	isLoading,
	error,
	empty,
	showNotes = false,
}: FeeTransactionsTableProps) {
	const columns: DataTableColumn<FeeTransaction>[] = [
		{
			id: 'period',
			header: 'Período',
			className: 'font-mono',
			cell: (row) => `#${row.billing_period_id}`,
		},
		{
			id: 'amount',
			header: 'Monto',
			className: cn(MONEY, 'font-medium'),
			cell: (row) => formatPrice(row.amount),
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => (
				<Badge variant={FEE_STATUS_VARIANTS[row.status] ?? 'outline'}>
					{FEE_STATUS_LABELS[row.status] ?? row.status}
				</Badge>
			),
		},
		{ id: 'charged', header: 'Cobrada', cell: (row) => formatDate(row.charged_at) },
		{ id: 'created', header: 'Registrada', cell: (row) => formatDate(row.created_at) },
	];

	if (showNotes) {
		columns.splice(4, 0, {
			id: 'notes',
			header: 'Notas',
			cell: (row) =>
				row.notes ? (
					<span className="whitespace-normal text-muted-foreground">{row.notes}</span>
				) : (
					<span className="text-muted-foreground">—</span>
				),
		});
	}

	return (
		<DataTable
			columns={columns}
			rows={rows}
			getRowId={(row) => row.id}
			isLoading={isLoading}
			error={error}
			errorTitle="No pudimos cargar las comisiones"
			empty={empty}
		/>
	);
}
