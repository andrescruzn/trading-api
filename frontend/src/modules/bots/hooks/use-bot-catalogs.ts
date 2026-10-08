import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import type { BotCatalogs } from '@/modules/bots/lib/bots-labels';
import {
	useSymbolsQuery,
	useTimeframesQuery,
} from '@/modules/market/hooks/use-market-queries';
import { useStrategiesQuery } from '@/modules/strategies/hooks/use-strategies-queries';

function toNameMap<T extends { id: number }>(
	items: T[] | undefined,
	getName: (item: T) => string,
): Map<number, string> {
	const map = new Map<number, string>();
	for (const item of items ?? []) map.set(item.id, getName(item));
	return map;
}

/**
 * Mapas `id → nombre` de los catálogos que referencia un bot (cuenta,
 * símbolo, timeframe, estrategia), para mostrar nombres en vez de IDs.
 * Reutiliza las queries cacheadas de cada módulo.
 */
function useBotCatalogs() {
	const accountsQuery = useAccountsQuery();
	const symbolsQuery = useSymbolsQuery();
	const timeframesQuery = useTimeframesQuery();
	const strategiesQuery = useStrategiesQuery();

	const catalogs: BotCatalogs = {
		accounts: toNameMap(accountsQuery.data, (account) => account.name),
		symbols: toNameMap(symbolsQuery.data, (symbol) => symbol.symbol),
		timeframes: toNameMap(timeframesQuery.data, (timeframe) => timeframe.code),
		strategies: toNameMap(
			strategiesQuery.data,
			(strategy) => `${strategy.name} v${strategy.version}`,
		),
	};

	return { accountsQuery, catalogs };
}

export { useBotCatalogs };
