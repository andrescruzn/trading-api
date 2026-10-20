import type { ReactNode } from 'react';
import type { CapitalMovement } from '@/modules/billing/api/billing.api';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { formatDateTime, formatPrice } from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';

const KIND_LABELS = { deposit: 'Aporte', withdrawal: 'Retiro' } as const;

const columns: DataTableColumn<CapitalMovement>[] = [
	{
		id: 'ts',
		header: 'Fecha',
		className: 'whitespace-nowrap',
		cell: (row) => formatDateTime(row.ts),
		skeletonClassName: 'w-32',
	},
	{
		id: 'kind',
		header: 'Tipo',
		cell: (row) => (
			<Badge variant={row.kind === 'deposit' ? 'secondary' : 'outline'}>
				{KIND_LABELS[row.kind]}
			</Badge>
		),
	},
	{
		id: 'amount',
		header: 'Monto',
		className: 'text-right font-mono tabular-nums',
		cell: (row) =>
			`${row.kind === 'withdrawal' ? '-' : '+'}${formatPrice(row.amount)}`,
	},
	{
		id: 'notes',
		header: 'Notas',
		cell: (row) =>
			row.notes ? (
				<span className="whitespace-normal text-muted-foreground">
					{row.notes}
				</span>
			) : (
				<span className="text-muted-foreground">—</span>
			),
	},
];

type CapitalMovementsTableProps = {
	rows: CapitalMovement[] | undefined;
	isLoading: boolean;
	error: unknown;
	empty: ReactNode;
};

export function CapitalMovementsTable({
	rows,
	isLoading,
	error,
	empty,
}: CapitalMovementsTableProps) {
	return (
		<DataTable
			columns={columns}
			rows={rows}
			getRowId={(row) => row.id}
			isLoading={isLoading}
			error={error}
			errorTitle="No pudimos cargar los aportes y retiros"
			empty={empty}
		/>
	);
}
