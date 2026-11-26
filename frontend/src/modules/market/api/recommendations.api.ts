import type { AssetClass } from '@/modules/market/api/market.api';
import { api } from '@/modules/shared/lib/api-client';

/** Un mercado recomendado por la IA, con la estrategia sugerida. */
type RecommendationItem = {
	symbol_id: number;
	symbol: string;
	strategy_id: number;
	strategy_name: string;
	strategy_version: string;
	/** Timeframe de la estrategia (el agente lo hereda). */
	timeframe: string | null;
	/** Confianza de la IA de 0 a 1; `null` si dio un valor inválido. */
	confidence: number | null;
	reasoning: string;
	risks: string;
};

type MarketRecommendation = {
	id: number;
	created_at: string | null;
	/** Filtro de clase usado al pedirla; `null` = todas. */
	asset_class: AssetClass | null;
	summary: string;
	items: RecommendationItem[];
	llm_provider: string | null;
	llm_model: string | null;
	llm_latency_ms: number | null;
};

type LatestRecommendationResponse = {
	recommendation: MarketRecommendation | null;
};

// ======================================================================
// Recomendaciones de mercados de la IA (M6, se muestran en el explorador)
// ======================================================================

/** Última recomendación guardada; `null` si nadie la ha pedido aún. */
async function getLatestMarketRecommendation() {
	const data = await api.get<LatestRecommendationResponse>(
		'/recommendations/markets/latest',
	);
	return data.recommendation;
}

/** Pide recomendaciones nuevas a la IA (llamada al LLM). Solo super admin. */
function generateMarketRecommendations(input: { asset_class?: AssetClass }) {
	return api.post<MarketRecommendation>('/recommendations/markets', input);
}

export type { MarketRecommendation, RecommendationItem };
export { generateMarketRecommendations, getLatestMarketRecommendation };
