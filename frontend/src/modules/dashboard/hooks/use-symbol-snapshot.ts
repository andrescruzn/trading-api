import { useMemo } from 'react';
import { useCandleFeaturesQuery } from '@/modules/features/hooks/use-features-queries';
import type { Regime } from '@/modules/features/lib/regime';
import { useCandlesQuery } from '@/modules/market/hooks/use-market-queries';

const SNAPSHOT_CANDLES = 48;

/**
 * Últimas velas de un símbolo + su régimen más reciente, para las tarjetas y
 * el gráfico del inicio. Las velas vienen de la más reciente a la más antigua:
 * aquí se ordenan cronológicamente.
 */
function useSymbolSnapshot(symbolId?: number, timeframeId?: number) {
	const candlesQuery = useCandlesQuery({
		symbol_id: symbolId,
		timeframe_id: timeframeId,
		limit: SNAPSHOT_CANDLES,
	});
	const featuresQuery = useCandleFeaturesQuery({
		symbol_id: symbolId,
		timeframe_id: timeframeId,
		limit: 1,
	});

	const candles = useMemo(
		() =>
			[...(candlesQuery.data ?? [])].sort(
				(a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime(),
			),
		[candlesQuery.data],
	);

	const last = candles.at(-1);
	const previous = candles.at(-2);
	const price = last ? Number(last.close) : null;
	const changePct =
		last && previous
			? ((Number(last.close) - Number(previous.close)) /
					Number(previous.close)) *
				100
			: null;

	return {
		candles,
		price,
		changePct,
		regime: (featuresQuery.data?.[0]?.features.regime ?? null) as Regime | null,
		isLoading: candlesQuery.isLoading,
		hasData: candles.length > 0,
	};
}

export { useSymbolSnapshot };
