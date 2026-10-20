import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import { useOwners } from '@/modules/auth/hooks/use-users-queries';
import { useBotCatalogs } from '@/modules/bots/hooks/use-bot-catalogs';
import { useBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { describeBot, describeBotMarket } from '@/modules/bots/lib/bots-labels';
import type {
	Order,
	OrderFilters,
	OrderSide,
	OrderStatus,
	OrderType,
} from '@/modules/orders/api/orders.api';
import { OrderFillsDialog } from '@/modules/orders/components/order-fills-dialog';
import { OrdersTable } from '@/modules/orders/components/orders-table';
import { useOrdersPageQuery } from '@/modules/orders/hooks/use-orders-queries';
import {
	ORDER_SIDE_OPTIONS,
	ORDER_STATUS_OPTIONS,
	ORDER_TYPE_OPTIONS,
} from '@/modules/orders/lib/orders-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { useServerPagination } from '@/modules/shared/hooks/use-server-pagination';
import { formatNumber } from '@/modules/shared/lib/format';

const ALL = 'all';

function filterValue<T extends string>(value: string) {
	return value === ALL ? undefined : (value as T);
}

export function AdminOrdersPage() {
	usePageBreadcrumb([
		{ label: 'Administración' },
		{ label: 'Todas las órdenes' },
	]);
	const botsQuery = useBotsQuery();
	const { accountsQuery, catalogs } = useBotCatalogs();
	const owners = useOwners(ALL);
	const [owner, setOwner] = useState(ALL);
	const [side, setSide] = useState(ALL);
	const [status, setStatus] = useState(ALL);
	const [type, setType] = useState(ALL);
	const [fillsOrder, setFillsOrder] = useState<Order | null>(null);

	// Filtros y paginación los resuelve el backend (solo admin sin `bot_id`).
	const filters: OrderFilters = {
		user_id: owner === ALL ? undefined : Number(owner),
		side: filterValue<OrderSide>(side),
		status: filterValue<OrderStatus>(status),
		type: filterValue<OrderType>(type),
	};
	const isFiltered =
		owner !== ALL || side !== ALL || status !== ALL || type !== ALL;
	const { params, tablePagination } = useServerPagination(
		JSON.stringify(filters),
	);
	const ordersQuery = useOrdersPageQuery(filters, params);
	const total = ordersQuery.data?.pagination.total;

	const botNames = new Map<number, string>();
	for (const bot of botsQuery.data ?? [])
		botNames.set(
			bot.id,
			`${describeBot(bot)} · ${describeBotMarket(bot, catalogs)}`,
		);

	// Dueño de una orden: orden → agente → cuenta → usuario.
	const accountOwner = new Map<number, number>();
	for (const account of accountsQuery.data ?? [])
		accountOwner.set(account.id, account.user_id);
	const botOwner = new Map<number, number>();
	for (const bot of botsQuery.data ?? []) {
		const userId = accountOwner.get(bot.account_id);
		if (userId !== undefined) botOwner.set(bot.id, userId);
	}
	const ownerOf = (order: Order) => botOwner.get(order.bot_id);

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Todas las órdenes"
				description={
					total === undefined
						? 'Todas las órdenes del sistema.'
						: isFiltered
							? `Todas las órdenes del sistema. ${formatNumber(total, 0)} con esos filtros.`
							: `Todas las órdenes del sistema. ${formatNumber(total, 0)} en total.`
				}
			/>
			<div className="grid gap-3 sm:grid-cols-2 lg:max-w-4xl lg:grid-cols-4">
				<OptionSelect
					aria-label="Dueño"
					size="sm"
					value={owner}
					onChange={(value) => setOwner(value ?? ALL)}
					options={owners.options}
				/>
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
				orders={ordersQuery.data?.items}
				isLoading={ordersQuery.isLoading}
				isFetching={ordersQuery.isPlaceholderData}
				error={ordersQuery.error}
				empty={
					isFiltered
						? 'No hay órdenes con esos filtros.'
						: 'Aún no hay órdenes en el sistema.'
				}
				onViewFills={setFillsOrder}
				botNames={botNames}
				renderOwner={(order) => (
					<OwnerCell userId={ownerOf(order)} users={owners.byId} />
				)}
				pagination={tablePagination(ordersQuery.data)}
			/>
			<OrderFillsDialog
				order={fillsOrder}
				onOpenChange={(open) => !open && setFillsOrder(null)}
			/>
		</div>
	);
}
