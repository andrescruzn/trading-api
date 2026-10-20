import { useQuery } from '@tanstack/react-query';
import {
	type BotFilters,
	getBot,
	listBots,
	listPendingSignals,
	listSharedBots,
	listSignals,
} from '@/modules/bots/api/bots.api';

const BOTS_QUERY_KEY = ['bots'] as const;
/** Bajo BOTS_QUERY_KEY: activar o apagar "Compartir señales" refresca la lista. */
const SHARED_BOTS_QUERY_KEY = [...BOTS_QUERY_KEY, 'shared'] as const;
const SIGNALS_QUERY_KEY = ['signals'] as const;
/** Bajo SIGNALS_QUERY_KEY: invalidar señales también refresca la cola. */
const PENDING_SIGNALS_QUERY_KEY = [...SIGNALS_QUERY_KEY, 'pending'] as const;

/** Cada 30 s: las señales automáticas llegan solas al cerrar cada vela. */
const PENDING_REFETCH_MS = 30_000;

/**
 * Sin filtros, un admin recibe los bots de todo el sistema: en pantallas de
 * usuario usa `useMyBotsQuery`.
 */
function useBotsQuery(
	filters: BotFilters = {},
	options: { enabled?: boolean } = {},
) {
	return useQuery({
		queryKey: [...BOTS_QUERY_KEY, filters],
		queryFn: () => listBots(filters),
		enabled: options.enabled ?? true,
	});
}

/**
 * Agentes (bots) de las cuentas del usuario autenticado, también para admin:
 * solo los suyos, no los de todo el sistema. Más recientes primero.
 */
function useMyBotsQuery(options: { enabled?: boolean } = {}) {
	return useBotsQuery({ mine: true }, options);
}

function useBotQuery(id: number | null) {
	return useQuery({
		queryKey: [...BOTS_QUERY_KEY, 'detail', id],
		queryFn: () => getBot(id as number),
		enabled: !!id,
	});
}

/** Últimas señales del bot; solo consulta cuando hay bot elegido. */
function useSignalsQuery(botId: number | null, limit = 50) {
	return useQuery({
		queryKey: [...SIGNALS_QUERY_KEY, { bot_id: botId, limit }],
		queryFn: () => listSignals({ bot_id: botId as number, limit }),
		enabled: !!botId,
	});
}

/** Cola de señales por aprobar de mis agentes. */
function usePendingSignalsQuery() {
	return useQuery({
		queryKey: PENDING_SIGNALS_QUERY_KEY,
		queryFn: listPendingSignals,
		refetchInterval: PENDING_REFETCH_MS,
	});
}

/** Agentes que comparten sus señales (de cualquier usuario, sin datos de cuenta). */
function useSharedBotsQuery(options: { enabled?: boolean } = {}) {
	return useQuery({
		queryKey: SHARED_BOTS_QUERY_KEY,
		queryFn: listSharedBots,
		enabled: options.enabled ?? true,
	});
}

export {
	BOTS_QUERY_KEY,
	PENDING_SIGNALS_QUERY_KEY,
	SHARED_BOTS_QUERY_KEY,
	SIGNALS_QUERY_KEY,
	useBotQuery,
	useBotsQuery,
	useMyBotsQuery,
	usePendingSignalsQuery,
	useSharedBotsQuery,
	useSignalsQuery,
};
