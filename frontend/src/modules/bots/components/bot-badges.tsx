import type {
	BotMode,
	BotStatus,
	SignalAction,
} from '@/modules/bots/api/bots.api';
import {
	BOT_MODE_LABELS,
	BOT_STATUS_LABELS,
	BOT_STATUS_VARIANTS,
	SIGNAL_ACTION_LABELS,
} from '@/modules/bots/lib/bots-labels';
import { Badge } from '@/modules/ui/components/badge';

export function BotStatusBadge({ status }: { status: BotStatus }) {
	return (
		<Badge variant={BOT_STATUS_VARIANTS[status] ?? 'outline'}>
			{BOT_STATUS_LABELS[status] ?? status}
		</Badge>
	);
}

/** Live va resaltado: opera con dinero real. */
export function BotModeBadge({ mode }: { mode: BotMode }) {
	return (
		<Badge variant={mode === 'live' ? 'destructive' : 'secondary'}>
			{BOT_MODE_LABELS[mode] ?? mode}
		</Badge>
	);
}

export function SignalActionBadge({ action }: { action: SignalAction }) {
	const label = SIGNAL_ACTION_LABELS[action] ?? action;
	if (action === 'buy') {
		return (
			<Badge variant="outline" className="border-chart-1/40 text-chart-1">
				{label}
			</Badge>
		);
	}
	return (
		<Badge variant={action === 'sell' ? 'destructive' : 'secondary'}>
			{label}
		</Badge>
	);
}

/**
 * Punto de estado del agente: late mientras está activo (analizando el
 * mercado), fijo cuando está pausado y apagado si está detenido.
 */
export function AgentStatusDot({ status }: { status: BotStatus }) {
	const color =
		status === 'running'
			? 'bg-chart-1'
			: status === 'paused'
				? 'bg-muted-foreground'
				: status === 'error'
					? 'bg-destructive'
					: 'bg-border';
	return (
		<span className="relative flex size-2.5 shrink-0" aria-hidden>
			{status === 'running' && (
				<span className="absolute inline-flex size-full animate-ping rounded-full bg-chart-1 opacity-60" />
			)}
			<span className={`relative inline-flex size-2.5 rounded-full ${color}`} />
		</span>
	);
}
