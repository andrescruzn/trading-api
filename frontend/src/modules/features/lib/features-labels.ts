import type {
	FeatureSet,
	FeatureSetFocus,
	IndicatorGroup,
} from '@/modules/features/api/features.api';
import type { SelectOption } from '@/modules/shared/components/option-select';

/** `default · v1.0.0`. */
function featureSetLabel(
	featureSet: Pick<FeatureSet, 'name' | 'version'>,
): string {
	return `${featureSet.name} · v${featureSet.version}`;
}

function featureSetOptions(
	featureSets: FeatureSet[] | undefined,
): SelectOption[] {
	return (featureSets ?? []).map((featureSet) => ({
		value: String(featureSet.id),
		label: featureSetLabel(featureSet),
	}));
}

/**
 * Valida que el texto sea un objeto JSON (no arreglo ni valor suelto), como
 * exige `spec: dict` en el backend. Devuelve el mensaje de error o `null`.
 */
function jsonObjectError(value: string): string | null {
	try {
		const parsed: unknown = JSON.parse(value);
		if (
			typeof parsed !== 'object' ||
			parsed === null ||
			Array.isArray(parsed)
		) {
			return 'Debe ser un objeto JSON, entre llaves { }';
		}
		return null;
	} catch {
		return 'El JSON no es válido. Revisa comillas, comas y llaves';
	}
}

/** Nombre corto de cada grupo de indicadores, para chips y listas. */
const INDICATOR_GROUP_LABELS: Record<IndicatorGroup, string> = {
	rsi: 'RSI',
	ema: 'EMA 20/50/200',
	macd: 'MACD',
	atr: 'ATR',
	bbands: 'Bollinger',
	vol_rel: 'Volumen relativo',
};

/** Qué mide cada grupo, en una frase y sin jerga (página Indicadores y asistente). */
const INDICATOR_GROUP_HINTS: Record<IndicatorGroup, string> = {
	rsi: 'Mide si el precio subió o bajó demasiado rápido (sobrecompra o sobreventa).',
	ema: 'Medias móviles: muestran la dirección de la tendencia a corto, medio y largo plazo.',
	macd: 'Compara dos medias para detectar cuándo la tendencia gana o pierde fuerza.',
	atr: 'Mide cuánto se mueve el precio por vela (volatilidad); ayuda a ubicar el stop loss.',
	bbands:
		'Bandas alrededor del precio: tocarlas suele indicar un extremo del rango.',
	vol_rel:
		'Volumen de la vela frente al promedio: confirma si el movimiento tiene respaldo.',
};

const FEATURE_SET_FOCUS_LABELS: Record<FeatureSetFocus, string> = {
	all: 'Cualquier estrategia',
	trend_following: 'Seguimiento de tendencia',
	mean_reversion: 'Reversión a la media',
};

export {
	FEATURE_SET_FOCUS_LABELS,
	featureSetLabel,
	featureSetOptions,
	INDICATOR_GROUP_HINTS,
	INDICATOR_GROUP_LABELS,
	jsonObjectError,
};
