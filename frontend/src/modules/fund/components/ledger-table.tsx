import type { LedgerEntry } from '@/modules/fund/api/fund.api';
import {
	LEDGER_BUCKET_LABELS,
	LEDGER_ENTRY_TYPE_LABELS,
} from '@/modules/fund/lib/fund-labels';
import {
	DataTable,
	type DataTableColumn,
	type ServerPagination,
} from '@/modules/shared/components/data-table';
import { formatDateTime, formatNumber } from '@/modules/shared/lib/format';
import { cn } from '@/modules/ui/lib/utils';

const COLUMNS: DataTableColumn<LedgerEntry>[] = [
	{
		id: 'created',
		header: 'Fecha',
		className: 'whitespace-nowrap',
		cell: (row) => formatDateTime(row.created_at),
	},
	{
		id: 'type',
		header: 'Movimiento',
		cell: (row) => LEDGER_ENTRY_TYPE_LABELS[row.entry_type] ?? row.entry_type,
	},
	{
		id: 'bucket',
		header: 'Saldo',
		cell: (row) => LEDGER_BUCKET_LABELS[row.bucket] ?? row.bucket,
	},
	{
		id: 'amount',
		header: 'Monto',
		className: 'text-right tabular-nums font-medium',
		cell: (row) => {
			const value = Number(row.amount);
			return (
				<span className={cn(value >= 0 ? 'text-chart-1' : 'text-destructive')}>
					{value >= 0 ? '+' : '−'}
					{formatNumber(Math.abs(value))} {row.asset}
				</span>
			);
		},
	},
	{
		id: 'description',
		header: 'Detalle',
		className: 'max-w-80 truncate',
		cell: (row) => (
			<span title={row.description ?? undefined}>{row.description ?? '—'}</span>
		),
	},
];

type LedgerTableProps = {
	rows: LedgerEntry[] | undefined;
	isLoading: boolean;
	isFetching?: boolean;
	error: unknown;
	pagination: ServerPagination;
};

/** Libro mayor de una persona: cada movimiento, nunca editado. */
export function LedgerTable({
	rows,
	isLoading,
	isFetching,
	error,
	pagination,
}: LedgerTableProps) {
	return (
		<DataTable
			columns={COLUMNS}
			rows={rows}
			getRowId={(row) => row.id}
			isLoading={isLoading}
			isFetching={isFetching}
			error={error}
			errorTitle="No pudimos cargar los movimientos"
			empty="Aún no hay movimientos."
			pagination={pagination}
		/>
	);
}
