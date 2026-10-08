import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// ======================================================================

type AnalysisDecision = 'APPROVED' | 'REJECTED';

/** Código estable de la fase que rechazó la operación (`null` si se aprobó). */
type RejectionReason =
	| 'REGIME_MISMATCH'
	| 'RULES_NOT_MET'
	| 'LLM_REJECTED'
	| 'RR_RATIO_TOO_LOW';

/** Valor libre: número, nombre de otro indicador (`ema_50`) o vacío. */
type RuleValue = number | string | boolean | null;

type RuleCheckDetail = {
	indicator: string;
	/** `lt` | `gt` | `lte` | `gte` | `eq` (otros fallan la regla). */
	operator: string;
	threshold: RuleValue;
	actual_value: RuleValue;
	passed: boolean;
};

/** Contexto con el que se evaluó la operación (snapshot del momento). */
type AnalysisMeta = {
	symbol: string;
	timeframe: string;
	strategy: string;
	strategy_version: string;
	account_mode: string;
	capital: number;
	base_currency: string;
	current_price: number;
	regime: string;
	features_snapshot: Record<string, number | string | null>;
};

/**
 * Los precios llegan como número (los calcula el agente, no son DECIMAL de la
 * base). Si una fase rechaza antes del agente de IA, vienen en `null`.
 */
type AnalysisResult = {
	decision: AnalysisDecision;
	rejection_reason: RejectionReason | null;
	entry: number | null;
	stop_loss: number | null;
	take_profit: number | null;
	position_size: number | null;
	rr_ratio: number | null;
	reasoning: string;
	/** 0–1, si el agente de IA la devolvió. */
	confidence: number | null;
	regime_check_passed: boolean;
	rules_check_passed: boolean;
	rr_check_passed: boolean;
	rules_detail: RuleCheckDetail[];
	meta: Partial<AnalysisMeta>;
};

type AnalyzeInput = {
	symbol_id: number;
	timeframe_id: number;
	strategy_id: number;
	account_id: number;
	feature_set_id: number;
};

/**
 * Corre las cuatro fases (régimen → reglas → agente de IA → R/R). Responde 200
 * tanto si aprueba como si rechaza; los errores (sin velas, sin balance, fallo
 * del proveedor de IA) llegan como 4xx/5xx con su `msg`.
 */
function analyze(input: AnalyzeInput) {
	return api.post<AnalysisResult>('/agent/analyze', input);
}

export type {
	AnalysisDecision,
	AnalysisMeta,
	AnalysisResult,
	AnalyzeInput,
	RejectionReason,
	RuleCheckDetail,
	RuleValue,
};
export { analyze };
