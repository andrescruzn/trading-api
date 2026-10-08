import {
	REGIME_BADGE_VARIANT,
	REGIME_LABELS,
	type Regime,
} from '@/modules/features/lib/regime';
import { Badge } from '@/modules/ui/components/badge';

/** Régimen requerido por la estrategia; sin régimen = opera en cualquiera. */
export function StrategyRegimeBadge({ regime }: { regime: string | null | undefined }) {
	if (!regime) {
		return <span className="text-muted-foreground">Cualquiera</span>;
	}
	if (!(regime in REGIME_LABELS)) {
		return <Badge variant="outline">{regime}</Badge>;
	}
	const known = regime as Regime;
	return (
		<Badge variant={REGIME_BADGE_VARIANT[known]}>{REGIME_LABELS[known]}</Badge>
	);
}
