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
		<Badge variant={action === 'sell' ? 'destructive' : 'secondary'}>{label}</Badge>
	);
}
