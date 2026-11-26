import type { TierCharge } from '@/modules/fund/api/fund.api';
import type { FeeSchedule } from '@/modules/fund/api/fund-payouts.api';
import { describeTier } from '@/modules/fund/lib/fund-payouts-labels';
import { formatDateTime, formatNumber } from '@/modules/shared/lib/format';

/** La tabla vigente: cada tramo de ganancia paga su %, como los impuestos. */
export function FeeScheduleTiers({ schedule }: { schedule: FeeSchedule }) {
	return (
		<div className="flex flex-col gap-2">
			<ul className="flex flex-col gap-1.5">
				{schedule.tiers.map((tier, index) => (
					<li
						key={tier.from_return_pct}
						className="rounded-md border px-3 py-2 text-sm tabular-nums"
					>
						{describeTier(
							tier.from_return_pct,
							schedule.tiers[index + 1]?.from_return_pct ?? null,
							tier.rate_pct,
						)}
					</li>
				))}
			</ul>
			<p className="text-xs text-muted-foreground">
				Vigente desde el {formatDateTime(schedule.created_at)}. Cada tramo cobra
				solo la parte de la ganancia que cae en él: ganar más nunca te deja
				menos neto. Si sales con pérdida, no hay comisión.
				{schedule.note ? ` ${schedule.note}` : ''}
			</p>
		</div>
	);
}

/** Cuánto cobró cada tramo en una salida concreta. */
export function FeeBreakdown({ breakdown }: { breakdown: TierCharge[] }) {
	if (breakdown.length === 0) {
		return (
			<span className="text-xs text-muted-foreground">
				Sin ganancia: no se cobró comisión.
			</span>
		);
	}
	return (
		<ul className="flex flex-col gap-0.5 text-xs text-muted-foreground tabular-nums">
			{breakdown.map((charge) => (
				<li key={charge.from_return_pct}>
					{describeTier(
						charge.from_return_pct,
						charge.to_return_pct,
						charge.rate_pct,
					)}
					: {formatNumber(charge.base, 2)} → {formatNumber(charge.fee, 2)} USDT
				</li>
			))}
		</ul>
	);
}
