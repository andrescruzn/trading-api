import { useQuery } from '@tanstack/react-query';
import {
	type BotFilters,
	getBot,
	listBots,
	listSignals,
} from '@/modules/bots/api/bots.api';

const BOTS_QUERY_KEY = ['bots'] as const;
const SIGNALS_QUERY_KEY = ['signals'] as const;

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

export {
	BOTS_QUERY_KEY,
	SIGNALS_QUERY_KEY,
	useBotQuery,
	useBotsQuery,
	useMyBotsQuery,
	useSignalsQuery,
};
