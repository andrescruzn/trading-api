import { useQueries, useQuery } from '@tanstack/react-query';
import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import {
	type Bot,
	getBot,
	listBots,
	listSignals,
} from '@/modules/bots/api/bots.api';

const BOTS_QUERY_KEY = ['bots'] as const;
const SIGNALS_QUERY_KEY = ['signals'] as const;

/**
 * Sin `account_id` solo funciona para admin (el backend responde 400 a los
 * demás roles): en pantallas de usuario usa `useMyBotsQuery`.
 */
function useBotsQuery(
	filters: { account_id?: number } = {},
	options: { enabled?: boolean } = {},
) {
	return useQuery({
		queryKey: [...BOTS_QUERY_KEY, filters],
		queryFn: () => listBots(filters),
		enabled: options.enabled ?? true,
	});
}

/**
 * Bots de varias cuentas en una sola lista. El backend exige `account_id`
 * a los usuarios, así que se pide una lista por cuenta y se unen (más
 * recientes primero). Comparte caché con `useBotsQuery({ account_id })`.
 */
function useBotsByAccountsQuery(accountIds: number[]) {
	return useQueries({
		queries: accountIds.map((account_id) => ({
			queryKey: [...BOTS_QUERY_KEY, { account_id }],
			queryFn: () => listBots({ account_id }),
		})),
		combine: (results) => {
			const isLoading = results.some((result) => result.isLoading);
			const error = results.find((result) => result.error)?.error ?? null;
			const data: Bot[] | undefined = isLoading
				? undefined
				: results
						.flatMap((result) => result.data ?? [])
						.sort((a, b) => b.id - a.id);
			return { data, isLoading, error };
		},
	});
}

/**
 * Bots de las cuentas del usuario autenticado (también para admin: solo las
 * suyas, no las de todo el sistema). Para selects y nombres en pantallas de
 * usuario como Alertas.
 */
function useMyBotsQuery(options: { enabled?: boolean } = {}) {
	const { user } = useAuth();
	const accountsQuery = useAccountsQuery();
	const enabled = options.enabled ?? true;
	const accountIds = enabled
		? (accountsQuery.data ?? [])
				.filter((account) => account.user_id === user?.id)
				.map((account) => account.id)
		: [];
	const botsQuery = useBotsByAccountsQuery(accountIds);
	return {
		data: botsQuery.data,
		isLoading: accountsQuery.isLoading || botsQuery.isLoading,
		error: accountsQuery.error ?? botsQuery.error,
	};
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
	useBotsByAccountsQuery,
	useBotsQuery,
	useMyBotsQuery,
	useSignalsQuery,
};
