import { IconReceipt, IconX } from '@tabler/icons-react';
import { type ReactNode, useState } from 'react';
import type { Order } from '@/modules/orders/api/orders.api';
import { CancelOrderDialog } from '@/modules/orders/components/cancel-order-dialog';
import {
	OrderSideBadge,
	OrderStatusBadge,
} from '@/modules/orders/components/order-badges';
import {
	isCancelable,
	ORDER_TYPE_LABELS,
} from '@/modules/orders/lib/orders-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import {
	formatDateTime,
	formatNumber,
	formatPrice,
} from '@/modules/shared/lib/format';
import { Button } from '@/modules/ui/components/button';

const NUMERIC = 'text-right font-mono tabular-nums';

type OrdersTableProps = {
	orders: Order[] | undefined;
	isLoading: boolean;
	error: unknown;
	empty: ReactNode;
	onViewFills: (order: Order) => void;
	/** Si se pasa, agrega la columna "Agente" con estos nombres (`id → nombre`). */
	botNames?: Map<number, string>;
	/** Si se pasa, agrega la columna "Dueño" (vistas de Supervisión). */
	renderOwner?: (order: Order) => ReactNode;
};

export function OrdersTable({
	orders,
	isLoading,
	error,
	empty,
	onViewFills,
	botNames,
	renderOwner,
}: OrdersTableProps) {
	const [canceling, setCanceling] = useState<Order | null>(null);
	const columns: DataTableColumn<Order>[] = [
		{
			id: 'id',
			header: 'ID',
			className: 'w-16 font-mono',
			cell: (row) => `#${row.id}`,
		},
		...(botNames
			? [
					{
						id: 'bot',
						header: 'Agente',
						cell: (row: Order) => botNames.get(row.bot_id) ?? `#${row.bot_id}`,
					},
				]
			: []),
		...(renderOwner
			? [{ id: 'owner', header: 'Dueño', cell: renderOwner }]
			: []),
		{
			id: 'side',
			header: 'Lado',
			cell: (row) => <OrderSideBadge side={row.side} />,
		},
		{
			id: 'type',
			header: 'Tipo',
			cell: (row) => ORDER_TYPE_LABELS[row.type] ?? row.type,
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => <OrderStatusBadge status={row.status} />,
		},
		{
			id: 'qty',
			header: 'Cantidad',
			className: NUMERIC,
			cell: (row) => formatNumber(row.qty),
		},
		{
			id: 'price',
			header: 'Precio',
			className: NUMERIC,
			cell: (row) => formatPrice(row.price),
		},
		{
			id: 'stop',
			header: 'Precio stop',
			className: NUMERIC,
			cell: (row) => formatPrice(row.stop_price),
		},
		{
			id: 'signal',
			header: 'Señal',
			className: 'font-mono text-muted-foreground',
			cell: (row) => (row.signal_id ? `#${row.signal_id}` : '—'),
		},
		{
			id: 'ts',
			header: 'Fecha',
			cell: (row) => formatDateTime(row.ts ?? row.created_at),
			skeletonClassName: 'w-32',
		},
		{
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) => (
				<div className="flex justify-end gap-1">
					{isCancelable(row) && (
						<Button
							variant="ghost"
							size="sm"
							className="text-destructive"
							onClick={() => setCanceling(row)}
						>
							<IconX />
							Cancelar
						</Button>
					)}
					<Button variant="ghost" size="sm" onClick={() => onViewFills(row)}>
						<IconReceipt />
						Ver ejecuciones
					</Button>
				</div>
			),
		},
	];

	return (
		<>
			<DataTable
				columns={columns}
				rows={orders}
				getRowId={(row) => row.id}
				isLoading={isLoading}
				error={error}
				errorTitle="No pudimos cargar las órdenes"
				empty={empty}
			/>
			<CancelOrderDialog
				order={canceling}
				onOpenChange={(open) => !open && setCanceling(null)}
			/>
		</>
	);
}
