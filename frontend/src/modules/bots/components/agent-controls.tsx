import {
	IconLoader2,
	IconPlayerPause,
	IconPlayerPlay,
	IconPlayerStop,
} from '@tabler/icons-react';
import { useState } from 'react';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import type { Bot, BotTransition } from '@/modules/bots/api/bots.api';
import { StopBotDialog } from '@/modules/bots/components/stop-bot-dialog';
import { useBotTransition } from '@/modules/bots/hooks/use-bot-transition';
import { canTransition } from '@/modules/bots/lib/bots-labels';
import { Button } from '@/modules/ui/components/button';

type AgentControlsProps = {
	bot: Bot;
	size?: 'xs' | 'sm';
	/** Oculta "Detener" (p. ej. en tarjetas compactas). */
	hideStop?: boolean;
};

const ICONS: Record<BotTransition, typeof IconPlayerPlay> = {
	start: IconPlayerPlay,
	pause: IconPlayerPause,
	stop: IconPlayerStop,
};

/**
 * Botones visibles para iniciar, pausar y detener un agente: solo aparecen
 * las transiciones que permite su estado actual. Detener pide confirmación.
 */
export function AgentControls({
	bot,
	size = 'sm',
	hideStop = false,
}: AgentControlsProps) {
	const canManage = useCanManage();
	const { run, isPending, pendingTransition } = useBotTransition(bot);
	const [confirmStop, setConfirmStop] = useState(false);

	// Solo un super admin cambia cosas: el socio ve el agente en solo lectura.
	if (!canManage) return null;

	function renderIcon(transition: BotTransition) {
		if (pendingTransition === transition) {
			return <IconLoader2 className="animate-spin" />;
		}
		const Icon = ICONS[transition];
		return <Icon />;
	}

	return (
		<div className="flex flex-wrap items-center gap-2">
			{canTransition(bot.status, 'start') && (
				<Button size={size} disabled={isPending} onClick={() => run('start')}>
					{renderIcon('start')}
					{bot.status === 'paused' ? 'Reanudar' : 'Iniciar'}
				</Button>
			)}
			{canTransition(bot.status, 'pause') && (
				<Button
					size={size}
					variant="outline"
					disabled={isPending}
					onClick={() => run('pause')}
				>
					{renderIcon('pause')}
					Pausar
				</Button>
			)}
			{!hideStop && canTransition(bot.status, 'stop') && (
				<Button
					size={size}
					variant="ghost"
					className="text-destructive hover:text-destructive"
					disabled={isPending}
					onClick={() => setConfirmStop(true)}
				>
					{renderIcon('stop')}
					Detener
				</Button>
			)}
			<StopBotDialog
				bot={bot}
				open={confirmStop}
				onOpenChange={setConfirmStop}
				isPending={isPending}
				onConfirm={() => run('stop', () => setConfirmStop(false))}
			/>
		</div>
	);
}
