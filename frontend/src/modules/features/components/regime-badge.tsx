import {
	REGIME_BADGE_VARIANT,
	REGIME_LABELS,
	type Regime,
} from '@/modules/features/lib/regime';
import { Badge } from '@/modules/ui/components/badge';

type RegimeBadgeProps = {
	regime: string | null | undefined;
	/** Texto cuando no hay régimen (por defecto `—`). */
	fallback?: string;
};

/** Badge del régimen de mercado; valores desconocidos se muestran tal cual. */
export function RegimeBadge({ regime, fallback = '—' }: RegimeBadgeProps) {
	if (!regime) {
		return <span className="text-muted-foreground">{fallback}</span>;
	}
	if (!(regime in REGIME_LABELS)) {
		return <Badge variant="outline">{regime}</Badge>;
	}
	const known = regime as Regime;
	return (
		<Badge variant={REGIME_BADGE_VARIANT[known]}>{REGIME_LABELS[known]}</Badge>
	);
}
