import { IconChevronRight } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import type { Bot } from '@/modules/bots/api/bots.api';
import { AgentControls } from '@/modules/bots/components/agent-controls';
import {
	AgentStatusDot,
	BotModeBadge,
	BotStatusBadge,
	SignalActionBadge,
} from '@/modules/bots/components/bot-badges';
import { useSignalsQuery } from '@/modules/bots/hooks/use-bots-queries';
import {
	type BotCatalogs,
	describeBot,
	describeBotMarket,
} from '@/modules/bots/lib/bots-labels';
import { formatDateTime } from '@/modules/shared/lib/format';
import { Button } from '@/modules/ui/components/button';
import { Card } from '@/modules/ui/components/card';
import { Skeleton } from '@/modules/ui/components/skeleton';
import { cn } from '@/modules/ui/lib/utils';

function LastSignal({ botId }: { botId: number }) {
	const signalsQuery = useSignalsQuery(botId, 1);
	const last = signalsQuery.data?.[0];

	if (signalsQuery.isLoading) return <Skeleton className="h-5 w-40" />;
	if (!last) {
		return <span className="text-muted-foreground">Aún sin señales</span>;
	}
	return (
		<span className="flex flex-wrap items-center gap-2">
			<SignalActionBadge action={last.action} />
			<span
				className={last.approved ? 'text-foreground' : 'text-muted-foreground'}
			>
				{last.approved ? 'Aprobada' : 'Rechazada'}
			</span>
			<span className="text-muted-foreground">· {formatDateTime(last.ts)}</span>
		</span>
	);
}

type AgentCardProps = {
	bot: Bot;
	catalogs: BotCatalogs;
	className?: string;
};

/**
 * Resumen de un agente: qué opera, con qué estrategia, su última señal y
 * los controles para iniciarlo o pausarlo sin entrar al detalle.
 */
export function AgentCard({ bot, catalogs, className }: AgentCardProps) {
	const strategy =
		catalogs.strategies.get(bot.strategy_id) ??
		`Estrategia #${bot.strategy_id}`;

	return (
		<Card
			className={cn(
				'group relative gap-4 p-5 transition-colors hover:border-primary/40',
				bot.status === 'running' && 'border-chart-1/30',
				className,
			)}
		>
			<div className="flex items-start justify-between gap-3">
				<div className="flex min-w-0 items-center gap-2.5">
					<AgentStatusDot status={bot.status} />
					<Link
						to="/agents/$agentId"
						params={{ agentId: String(bot.id) }}
						className="truncate font-semibold after:absolute after:inset-0 hover:underline"
					>
						{describeBot(bot)}
					</Link>
				</div>
				<div className="flex shrink-0 items-center gap-1.5">
					<BotStatusBadge status={bot.status} />
					<BotModeBadge mode={bot.mode} />
				</div>
			</div>

			<dl className="grid gap-2 text-sm">
				<div className="flex items-baseline justify-between gap-3">
					<dt className="text-muted-foreground">Opera</dt>
					<dd className="truncate font-mono font-medium">
						{describeBotMarket(bot, catalogs)}
					</dd>
				</div>
				<div className="flex items-baseline justify-between gap-3">
					<dt className="text-muted-foreground">Estrategia</dt>
					<dd className="truncate text-right">{strategy}</dd>
				</div>
				<div className="flex items-start justify-between gap-3">
					<dt className="shrink-0 text-muted-foreground">Última señal</dt>
					<dd className="text-right">
						<LastSignal botId={bot.id} />
					</dd>
				</div>
			</dl>

			{/* Por encima del enlace que cubre la tarjeta, para que los botones respondan. */}
			<div className="relative z-10 flex items-center justify-between gap-2 border-t pt-4">
				<AgentControls bot={bot} size="xs" hideStop />
				<Button
					size="xs"
					variant="ghost"
					render={
						<Link to="/agents/$agentId" params={{ agentId: String(bot.id) }} />
					}
				>
					Ver detalle
					<IconChevronRight />
				</Button>
			</div>
		</Card>
	);
}
