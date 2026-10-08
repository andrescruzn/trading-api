import { keepPreviousData, useQuery } from '@tanstack/react-query';
import {
	listFills,
	listOrders,
	listPositions,
	type OrderFilters,
} from '@/modules/orders/api/orders.api';

const ORDERS_QUERY_KEY = ['orders'] as const;
const POSITIONS_QUERY_KEY = ['positions'] as const;
const FILLS_QUERY_KEY = ['fills'] as const;

/** Admin: todas las órdenes (o las de un bot). */
function useOrdersQuery(filters: OrderFilters = {}) {
	return useQuery({
		queryKey: [...ORDERS_QUERY_KEY, filters],
		queryFn: () => listOrders(filters),
		placeholderData: keepPreviousData,
	});
}

/** Órdenes de un bot; solo consulta cuando hay bot elegido. */
function useBotOrdersQuery(botId: number | null) {
	return useQuery({
		queryKey: [...ORDERS_QUERY_KEY, { bot_id: botId }],
		queryFn: () => listOrders({ bot_id: botId as number }),
		enabled: !!botId,
	});
}

function useBotPositionsQuery(botId: number | null) {
	return useQuery({
		queryKey: [...POSITIONS_QUERY_KEY, { bot_id: botId }],
		queryFn: () => listPositions({ bot_id: botId as number }),
		enabled: !!botId,
	});
}

function useBotFillsQuery(botId: number | null) {
	return useQuery({
		queryKey: [...FILLS_QUERY_KEY, { bot_id: botId }],
		queryFn: () => listFills({ bot_id: botId as number }),
		enabled: !!botId,
	});
}

function useOrderFillsQuery(orderId: number | null) {
	return useQuery({
		queryKey: [...FILLS_QUERY_KEY, { order_id: orderId }],
		queryFn: () => listFills({ order_id: orderId as number }),
		enabled: !!orderId,
	});
}

export {
	FILLS_QUERY_KEY,
	ORDERS_QUERY_KEY,
	POSITIONS_QUERY_KEY,
	useBotFillsQuery,
	useBotOrdersQuery,
	useBotPositionsQuery,
	useOrderFillsQuery,
	useOrdersQuery,
};
