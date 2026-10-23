import { useCandleFeaturesQuery } from '@/modules/features/hooks/use-features-queries';
import { useCandlesQuery } from '@/modules/market/hooks/use-market-queries';
import { toTimestamp } from '@/modules/shared/lib/format';

// Precio y variación salen de las dos últimas velas.
const SNAPSHOT_CANDLES = 2;

/**
 * Último precio de un símbolo, su variación frente a la vela anterior y el
 * régimen más reciente, para la tarjeta de cada agente.
 */
function useSymbolSnapshot(
	symbolId: number,
	timeframeId: number,
	featureSetId?: number,
) {
	const candlesQuery = useCandlesQuery({
		symbol_id: symbolId,
		timeframe_id: timeframeId,
		limit: SNAPSHOT_CANDLES,
	});
	const featuresQuery = useCandleFeaturesQuery({
		symbol_id: symbolId,
		timeframe_id: timeframeId,
		feature_set_id: featureSetId,
		limit: 1,
	});

	// Se ordena igual por fecha para no depender del orden de la API.
	const [last, previous] = [...(candlesQuery.data ?? [])].sort(
		(a, b) => (toTimestamp(b.ts) ?? 0) - (toTimestamp(a.ts) ?? 0),
	);
	const price = last ? Number(last.close) : null;
	const changePct =
		last && previous
			? ((Number(last.close) - Number(previous.close)) /
					Number(previous.close)) *
				100
			: null;

	return {
		price,
		changePct,
		regime: featuresQuery.data?.[0]?.features.regime ?? null,
		isLoading: candlesQuery.isLoading,
	};
}

export { useSymbolSnapshot };
