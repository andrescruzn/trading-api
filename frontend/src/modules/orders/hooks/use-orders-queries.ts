import { keepPreviousData, useQuery } from '@tanstack/react-query';
import {
	getBotPerformance,
	listFills,
	listOrdersPage,
	listPositions,
	listStrategyTrackRecord,
	type OrderFilters,
} from '@/modules/orders/api/orders.api';
import type { PageParams } from '@/modules/shared/types/api';

const ORDERS_QUERY_KEY = ['orders'] as const;
const POSITIONS_QUERY_KEY = ['positions'] as const;
const FILLS_QUERY_KEY = ['fills'] as const;

/**
 * Una página de órdenes (paginación en el servidor). Admin: todas o filtradas;
 * usuario: exige `bot_id`. Mientras llega la página nueva se ve la anterior.
 */
function useOrdersPageQuery(
	filters: OrderFilters,
	page: PageParams,
	options: { enabled?: boolean } = {},
) {
	return useQuery({
		queryKey: [...ORDERS_QUERY_KEY, 'page', filters, page],
		queryFn: () => listOrdersPage(filters, page),
		placeholderData: keepPreviousData,
		enabled: options.enabled ?? true,
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

// El rendimiento sale de los fills: vive bajo FILLS_QUERY_KEY para que crear,
// cancelar o aprobar órdenes (que invalidan los fills) también lo refresque.
function useBotPerformanceQuery(botId: number | null) {
	return useQuery({
		queryKey: [...FILLS_QUERY_KEY, 'performance', botId],
		queryFn: () => getBotPerformance(botId as number),
		enabled: !!botId,
	});
}

function useStrategyTrackRecordQuery(mode?: 'paper' | 'live') {
	return useQuery({
		queryKey: [...FILLS_QUERY_KEY, 'track-record', mode ?? 'all'],
		queryFn: () => listStrategyTrackRecord(mode ? { mode } : {}),
		placeholderData: keepPreviousData,
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
	useBotPerformanceQuery,
	useBotPositionsQuery,
	useOrderFillsQuery,
	useOrdersPageQuery,
	useStrategyTrackRecordQuery,
};
