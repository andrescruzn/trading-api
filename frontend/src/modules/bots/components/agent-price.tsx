import type { Bot } from '@/modules/bots/api/bots.api';
import { useSymbolSnapshot } from '@/modules/bots/hooks/use-symbol-snapshot';
import { RegimeBadge } from '@/modules/features/components/regime-badge';
import {
	formatPrice,
	formatSignedPercentValue,
} from '@/modules/shared/lib/format';
import { Skeleton } from '@/modules/ui/components/skeleton';
import { cn } from '@/modules/ui/lib/utils';

/** Último precio del mercado del agente, variación frente a la vela anterior y régimen. */
export function AgentPrice({ bot }: { bot: Bot }) {
	const snapshot = useSymbolSnapshot(
		bot.symbol_id,
		bot.timeframe_id,
		bot.feature_set_id ?? undefined,
	);

	if (snapshot.isLoading) return <Skeleton className="h-5 w-32" />;
	if (snapshot.price === null) {
		return <span className="text-muted-foreground">Sin datos aún</span>;
	}

	return (
		<span className="flex flex-wrap items-center justify-end gap-2">
			<span className="font-mono font-medium tabular-nums">
				{formatPrice(snapshot.price)}
			</span>
			{snapshot.changePct !== null && (
				<span
					className={cn(
						'tabular-nums',
						snapshot.changePct >= 0 ? 'text-chart-1' : 'text-destructive',
					)}
				>
					{formatSignedPercentValue(snapshot.changePct)}
				</span>
			)}
			{snapshot.regime && <RegimeBadge regime={snapshot.regime} />}
		</span>
	);
}
