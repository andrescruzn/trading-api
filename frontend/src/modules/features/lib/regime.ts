import type { SelectOption } from '@/modules/shared/components/option-select';

/** Régimen de mercado que calcula M3 (`features.regime`). */
type Regime = 'trend_up' | 'trend_down' | 'sideways';

const REGIME_LABELS: Record<Regime, string> = {
	trend_up: 'Tendencia alcista',
	trend_down: 'Tendencia bajista',
	sideways: 'Lateral',
};

/**
 * Variante de `Badge` por régimen (solo tokens del tema): alcista con el
 * color primario, bajista en rojo, lateral neutro.
 */
const REGIME_BADGE_VARIANT: Record<Regime, 'default' | 'destructive' | 'secondary'> = {
	trend_up: 'default',
	trend_down: 'destructive',
	sideways: 'secondary',
};

const REGIME_OPTIONS: SelectOption[] = Object.entries(REGIME_LABELS).map(
	([value, label]) => ({ value, label }),
);

function regimeLabel(regime: string | null | undefined): string {
	if (!regime) return '—';
	return REGIME_LABELS[regime as Regime] ?? regime;
}

export type { Regime };
export { REGIME_BADGE_VARIANT, REGIME_LABELS, REGIME_OPTIONS, regimeLabel };
