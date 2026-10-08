import type { ReactNode } from 'react';
import type { Fill } from '@/modules/orders/api/orders.api';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { formatDateTime, formatNumber, formatPrice } from '@/modules/shared/lib/format';

const NUMERIC = 'text-right font-mono tabular-nums';

const columns: DataTableColumn<Fill>[] = [
	{ id: 'id', header: 'ID', className: 'w-16 font-mono', cell: (row) => `#${row.id}` },
	{ id: 'order', header: 'Orden', className: 'font-mono', cell: (row) => `#${row.order_id}` },
	{ id: 'qty', header: 'Cantidad', className: NUMERIC, cell: (row) => formatNumber(row.qty) },
	{ id: 'price', header: 'Precio', className: NUMERIC, cell: (row) => formatPrice(row.price) },
	{
		id: 'notional',
		header: 'Nocional',
		className: NUMERIC,
		cell: (row) => formatPrice(row.notional_value),
	},
	{
		id: 'fee',
		header: 'Comisión',
		className: NUMERIC,
		cell: (row) => (
			<>
				{formatNumber(row.fee)}
				{row.fee_asset && (
					<span className="ml-1 text-xs text-muted-foreground">{row.fee_asset}</span>
				)}
			</>
		),
	},
	{
		id: 'ts',
		header: 'Fecha',
		cell: (row) => formatDateTime(row.ts),
		skeletonClassName: 'w-32',
	},
];

type FillsTableProps = {
	fills: Fill[] | undefined;
	isLoading: boolean;
	error: unknown;
	empty: ReactNode;
	/** Oculta la columna "Orden" (p. ej. en el diálogo de una sola orden). */
	hideOrder?: boolean;
};

/** Tabla de ejecuciones (fills) de una orden o de un bot. */
export function FillsTable({ fills, isLoading, error, empty, hideOrder }: FillsTableProps) {
	return (
		<DataTable
			columns={hideOrder ? columns.filter((column) => column.id !== 'order') : columns}
			rows={fills}
			getRowId={(row) => row.id}
			isLoading={isLoading}
			error={error}
			errorTitle="No pudimos cargar las ejecuciones"
			empty={empty}
		/>
	);
}
