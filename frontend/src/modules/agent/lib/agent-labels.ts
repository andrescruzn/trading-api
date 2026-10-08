import type {
	AnalysisResult,
	RejectionReason,
	RuleValue,
} from '@/modules/agent/api/agent.api';
import { formatNumber } from '@/modules/shared/lib/format';

/** Mínimo de riesgo/beneficio de la regla de negocio (2:1). */
const MIN_RR_RATIO = 2;

const REJECTION_REASON_LABELS: Record<RejectionReason, string> = {
	REGIME_MISMATCH:
		'El régimen del mercado no coincide con el que exige la estrategia.',
	RULES_NOT_MET: 'No se cumplen todas las reglas de la estrategia.',
	LLM_REJECTED:
		'El agente de IA no encontró una operación clara con los datos actuales.',
	RR_RATIO_TOO_LOW: `La operación no cumple el riesgo/beneficio mínimo de ${MIN_RR_RATIO}:1.`,
};

const RULE_OPERATOR_SYMBOLS: Record<string, string> = {
	lt: '<',
	gt: '>',
	lte: '≤',
	gte: '≥',
	eq: '=',
};

type PhaseStatus = 'pass' | 'fail' | 'skipped';

type AnalysisPhase = {
	id: 'regime' | 'rules' | 'llm' | 'rr';
	label: string;
	status: PhaseStatus;
};

const PHASE_STATUS_LABELS: Record<PhaseStatus, string> = {
	pass: 'cumplida',
	fail: 'no cumplida',
	skipped: 'no evaluada',
};

function rejectionReasonLabel(result: AnalysisResult): string | null {
	const reason = result.rejection_reason;
	if (!reason) return null;
	if (reason === 'RR_RATIO_TOO_LOW' && result.rr_ratio !== null) {
		return `Riesgo/beneficio ${formatRiskReward(result.rr_ratio)}: por debajo del mínimo de ${MIN_RR_RATIO}:1.`;
	}
	return (
		REJECTION_REASON_LABELS[reason] ??
		'La operación no pasó una de las fases del análisis.'
	);
}

/**
 * Las fases corren en orden y el análisis se detiene en la primera que
 * falla: las siguientes quedan "no evaluadas", no "no cumplidas".
 */
function analysisPhases(result: AnalysisResult): AnalysisPhase[] {
	const reason = result.rejection_reason;
	const regime: PhaseStatus = result.regime_check_passed ? 'pass' : 'fail';
	const rules: PhaseStatus = result.rules_check_passed
		? 'pass'
		: regime === 'pass'
			? 'fail'
			: 'skipped';
	const llm: PhaseStatus =
		reason === 'LLM_REJECTED' ? 'fail' : rules === 'pass' ? 'pass' : 'skipped';
	const rr: PhaseStatus = result.rr_check_passed
		? 'pass'
		: reason === 'RR_RATIO_TOO_LOW'
			? 'fail'
			: 'skipped';

	return [
		{ id: 'regime', label: 'Régimen', status: regime },
		{ id: 'rules', label: 'Reglas', status: rules },
		{ id: 'llm', label: 'Agente de IA', status: llm },
		{ id: 'rr', label: `R/R ≥ ${MIN_RR_RATIO}:1`, status: rr },
	];
}

/** `2.4567` → `2,46:1`. */
function formatRiskReward(ratio: number | null): string {
	if (ratio === null) return '—';
	return `${formatNumber(ratio, 2)}:1`;
}

/** Umbral o valor de una regla: número formateado o nombre de indicador. */
function formatRuleValue(value: RuleValue): string {
	if (value === null || value === '') return '—';
	if (typeof value === 'number') return formatNumber(value);
	if (typeof value === 'boolean') return value ? 'Sí' : 'No';
	return value;
}

function ruleOperatorSymbol(operator: string): string {
	return RULE_OPERATOR_SYMBOLS[operator] ?? operator;
}

export type { AnalysisPhase, PhaseStatus };
export {
	analysisPhases,
	formatRiskReward,
	formatRuleValue,
	MIN_RR_RATIO,
	PHASE_STATUS_LABELS,
	REJECTION_REASON_LABELS,
	rejectionReasonLabel,
	ruleOperatorSymbol,
};
