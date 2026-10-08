import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useBotCatalogs } from '@/modules/bots/hooks/use-bot-catalogs';
import { useBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { describeBot } from '@/modules/bots/lib/bots-labels';
import type { Order } from '@/modules/orders/api/orders.api';
import { OrderFillsDialog } from '@/modules/orders/components/order-fills-dialog';
import { OrdersTable } from '@/modules/orders/components/orders-table';
import { useOrdersQuery } from '@/modules/orders/hooks/use-orders-queries';
import {
	ORDER_SIDE_OPTIONS,
	ORDER_STATUS_OPTIONS,
	ORDER_TYPE_OPTIONS,
} from '@/modules/orders/lib/orders-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';

const ALL = 'all';

// Máximo que acepta `GET /orders`; el backend devuelve las más recientes.
const ORDERS_LIMIT = 500;

export function AdminOrdersPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Órdenes' }]);
	// Sin `bot_id` el backend devuelve todas las órdenes (solo admin).
	const ordersQuery = useOrdersQuery({ limit: ORDERS_LIMIT });
	const botsQuery = useBotsQuery();
	const { catalogs } = useBotCatalogs();
	const [side, setSide] = useState(ALL);
	const [status, setStatus] = useState(ALL);
	const [type, setType] = useState(ALL);
	const [fillsOrder, setFillsOrder] = useState<Order | null>(null);

	const botNames = new Map<number, string>();
	for (const bot of botsQuery.data ?? [])
		botNames.set(bot.id, describeBot(bot, catalogs));

	const allOrders = ordersQuery.data ?? [];
	const filteredOrders = allOrders.filter(
		(order) =>
			(side === ALL || order.side === side) &&
			(status === ALL || order.status === status) &&
			(type === ALL || order.type === type),
	);

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Órdenes"
				description={
					ordersQuery.data
						? `Todas las órdenes del sistema. ${filteredOrders.length} de ${allOrders.length} órdenes.`
						: 'Todas las órdenes del sistema.'
				}
			/>
			<div className="grid gap-3 sm:grid-cols-3 lg:max-w-3xl">
				<OptionSelect
					aria-label="Lado"
					size="sm"
					value={side}
					onChange={(value) => setSide(value ?? ALL)}
					options={[
						{ value: ALL, label: 'Todos los lados' },
						...ORDER_SIDE_OPTIONS,
					]}
				/>
				<OptionSelect
					aria-label="Estado"
					size="sm"
					value={status}
					onChange={(value) => setStatus(value ?? ALL)}
					options={[
						{ value: ALL, label: 'Todos los estados' },
						...ORDER_STATUS_OPTIONS,
					]}
				/>
				<OptionSelect
					aria-label="Tipo"
					size="sm"
					value={type}
					onChange={(value) => setType(value ?? ALL)}
					options={[
						{ value: ALL, label: 'Todos los tipos' },
						...ORDER_TYPE_OPTIONS,
					]}
				/>
			</div>
			<OrdersTable
				orders={ordersQuery.data ? filteredOrders : undefined}
				isLoading={ordersQuery.isLoading}
				error={ordersQuery.error}
				empty={
					allOrders.length > 0
						? 'No hay órdenes con esos filtros.'
						: 'Aún no hay órdenes en el sistema.'
				}
				onViewFills={setFillsOrder}
				botNames={botNames}
			/>
			<OrderFillsDialog
				order={fillsOrder}
				onOpenChange={(open) => !open && setFillsOrder(null)}
			/>
		</div>
	);
}
