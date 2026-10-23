import { useQuery } from '@tanstack/react-query';
import {
	getPool,
	getSettlementPreview,
	listEligibleAgents,
	listMyParticipations,
	listPools,
} from '@/modules/fund/api/fund.api';

const POOLS_QUERY_KEY = ['fund-pools'] as const;
const ELIGIBLE_AGENTS_QUERY_KEY = ['fund-eligible-agents'] as const;
const SETTLEMENT_PREVIEW_QUERY_KEY = ['fund-settlement-preview'] as const;
const PARTICIPATIONS_QUERY_KEY = ['fund-my-participations'] as const;

// El capital estimado cambia con cada operación del agente
const POOLS_REFETCH_MS = 60_000;

function usePoolsQuery() {
	return useQuery({
		queryKey: POOLS_QUERY_KEY,
		queryFn: listPools,
		refetchInterval: POOLS_REFETCH_MS,
	});
}

function usePoolQuery(poolId: number | null) {
	return useQuery({
		queryKey: [...POOLS_QUERY_KEY, poolId],
		queryFn: () => getPool(poolId as number),
		enabled: !!poolId,
		refetchInterval: POOLS_REFETCH_MS,
	});
}

/** Solo cuando el diálogo para abrir un agente está abierto. */
function useEligibleAgentsQuery(enabled: boolean) {
	return useQuery({
		queryKey: ELIGIBLE_AGENTS_QUERY_KEY,
		queryFn: listEligibleAgents,
		enabled,
	});
}

/** Se recalcula cada vez que se abre el diálogo de liquidar. */
function useSettlementPreviewQuery(poolId: number | null, enabled: boolean) {
	return useQuery({
		queryKey: [...SETTLEMENT_PREVIEW_QUERY_KEY, poolId],
		queryFn: () => getSettlementPreview(poolId as number),
		enabled: enabled && !!poolId,
		staleTime: 0,
	});
}

function useMyParticipationsQuery() {
	return useQuery({
		queryKey: PARTICIPATIONS_QUERY_KEY,
		queryFn: listMyParticipations,
		refetchInterval: POOLS_REFETCH_MS,
	});
}

export {
	ELIGIBLE_AGENTS_QUERY_KEY,
	PARTICIPATIONS_QUERY_KEY,
	POOLS_QUERY_KEY,
	SETTLEMENT_PREVIEW_QUERY_KEY,
	useEligibleAgentsQuery,
	useMyParticipationsQuery,
	usePoolQuery,
	usePoolsQuery,
	useSettlementPreviewQuery,
};
