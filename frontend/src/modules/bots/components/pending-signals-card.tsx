import { IconBell } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import {
	BotModeBadge,
	SignalActionBadge,
} from '@/modules/bots/components/bot-badges';
import { SignalDecisionActions } from '@/modules/bots/components/signal-decision-actions';
import { usePendingSignalsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { formatRiskReward } from '@/modules/bots/lib/bots-labels';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { formatPrice } from '@/modules/shared/lib/format';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';

/**
 * Cola de señales por aprobar (agentes en modo Con aprobación). Se oculta
 * cuando no hay ninguna: no ocupa el dashboard de quien no usa el modo.
 */
export function PendingSignalsCard() {
	const pendingQuery = usePendingSignalsQuery();
	const pending = pendingQuery.data ?? [];

	if (pendingQuery.error) {
		return (
			<ErrorAlert
				title="No pudimos cargar las señales por aprobar"
				error={pendingQuery.error}
			/>
		);
	}
	if (pending.length === 0) return null;

	return (
		<Card className="border-primary/40">
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<IconBell className="size-4" />
					Señales por aprobar · {pending.length}
				</CardTitle>
				<CardDescription>
					Al aprobar, la orden sale con el precio actual si todavía cumple el
					stop loss y el riesgo/beneficio mínimo.
				</CardDescription>
			</CardHeader>
			<CardContent>
				<ul className="flex flex-col divide-y">
					{pending.map((signal) => (
						<li
							key={signal.id}
							className="flex flex-col gap-3 py-3 first:pt-0 last:pb-0 lg:flex-row lg:items-center lg:justify-between"
						>
							<div className="flex min-w-0 flex-col gap-1">
								<div className="flex flex-wrap items-center gap-2">
									<SignalActionBadge action={signal.action} />
									<Link
										to="/agents/$agentId"
										params={{ agentId: String(signal.bot_id) }}
										className="truncate font-medium hover:underline"
									>
										{signal.bot_name}
									</Link>
									<BotModeBadge mode={signal.bot_mode} />
								</div>
								<p className="text-sm text-muted-foreground tabular-nums">
									Entrada {formatPrice(signal.entry_price)} · SL{' '}
									{formatPrice(signal.stop_loss)} · TP{' '}
									{formatPrice(signal.take_profit)} · R/R{' '}
									{formatRiskReward(signal.rr_ratio)}
								</p>
							</div>
							<SignalDecisionActions
								signal={signal}
								botMode={signal.bot_mode}
							/>
						</li>
					))}
				</ul>
			</CardContent>
		</Card>
	);
}
