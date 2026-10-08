import type { Regime } from '@/modules/features/lib/regime';
import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// ======================================================================

type FeatureSet = {
	id: number;
	name: string;
	version: string;
	description: string | null;
	/** Configuración JSON de los indicadores. */
	spec: Record<string, unknown>;
	created_at: string | null;
};

/** Indicadores calculados por vela (claves conocidas + extras del spec). */
type FeatureValues = {
	rsi_14?: number | null;
	ema_20?: number | null;
	ema_50?: number | null;
	ema_200?: number | null;
	macd?: number | null;
	macd_signal?: number | null;
	atr_14?: number | null;
	bb_upper?: number | null;
	bb_lower?: number | null;
	vol_rel?: number | null;
	regime?: Regime | null;
	[key: string]: unknown;
};

type CandleFeature = {
	id: number;
	symbol_id: number;
	timeframe_id: number;
	ts: string;
	feature_set_id: number;
	features: FeatureValues;
};

type CandleFeatureFilters = {
	symbol_id: number;
	timeframe_id: number;
	feature_set_id?: number;
	limit?: number;
};

type FeatureSetInput = {
	name: string;
	version: string;
	description: string | null;
	spec: Record<string, unknown>;
};

type CalculateFeaturesInput = {
	symbol_id: number;
	timeframe_id: number;
	feature_set_id: number;
};

type CalculateFeaturesResult = {
	symbol_id: number;
	timeframe_id: number;
	feature_set_id: number;
	candles_loaded: number;
	/** Velas con todos los indicadores calculados. */
	rows_calculated: number;
	/** Filas insertadas o actualizadas en la base (upsert). */
	rows_affected: number;
};

// ======================================================================
// Feature sets
// ======================================================================

function listFeatureSets() {
	return api.get<FeatureSet[]>('/feature-sets');
}

/** Solo admin. */
function createFeatureSet(input: FeatureSetInput) {
	return api.post<FeatureSet>('/feature-sets', input);
}

// ======================================================================
// Indicadores por vela
// ======================================================================

/** El backend las devuelve de la más reciente a la más antigua. */
function listCandleFeatures(filters: CandleFeatureFilters) {
	return api.get<CandleFeature[]>('/candle-features', filters);
}

/** Calcula y guarda los indicadores de las velas ya descargadas. Solo admin. */
function calculateFeatures(input: CalculateFeaturesInput) {
	return api.post<CalculateFeaturesResult>('/candle-features/calculate', input);
}

export type {
	CalculateFeaturesInput,
	CalculateFeaturesResult,
	CandleFeature,
	CandleFeatureFilters,
	FeatureSet,
	FeatureSetInput,
	FeatureValues,
};
export {
	calculateFeatures,
	createFeatureSet,
	listCandleFeatures,
	listFeatureSets,
};
