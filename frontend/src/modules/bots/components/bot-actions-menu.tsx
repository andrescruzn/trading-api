import {
	IconDots,
	IconEye,
	IconLoader2,
	IconPlayerPause,
	IconPlayerPlay,
	IconPlayerStop,
} from '@tabler/icons-react';
import { useState } from 'react';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import type { Bot } from '@/modules/bots/api/bots.api';
import { StopBotDialog } from '@/modules/bots/components/stop-bot-dialog';
import { useBotTransition } from '@/modules/bots/hooks/use-bot-transition';
import { canTransition, describeBot } from '@/modules/bots/lib/bots-labels';
import { Button } from '@/modules/ui/components/button';
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from '@/modules/ui/components/dropdown-menu';

type BotActionsMenuProps = {
	bot: Bot;
	/** Si se pasa, el menú incluye "Ver agente". */
	onView?: () => void;
};

/**
 * Menú de acciones de una fila de agente: iniciar, pausar y detener (con
 * confirmación). Las transiciones que el estado actual no permite quedan
 * deshabilitadas.
 */
export function BotActionsMenu({ bot, onView }: BotActionsMenuProps) {
	const canManage = useCanManage();
	const { run, isPending } = useBotTransition(bot);
	const [confirmStop, setConfirmStop] = useState(false);

	// El socio no inicia, pausa ni detiene: abre el agente con clic en la fila.
	if (!canManage) return null;

	return (
		// La fila de la tabla es clicable y los eventos del menú y del diálogo
		// suben por el árbol de React aunque se rendericen en un portal.
		<div
			className="flex justify-end"
			onClick={(event) => event.stopPropagation()}
		>
			<DropdownMenu>
				<DropdownMenuTrigger
					disabled={isPending}
					render={<Button variant="ghost" size="icon-sm" />}
				>
					{isPending ? <IconLoader2 className="animate-spin" /> : <IconDots />}
					<span className="sr-only">Acciones de {describeBot(bot)}</span>
				</DropdownMenuTrigger>
				<DropdownMenuContent align="end" className="w-auto min-w-44">
					{onView && (
						<>
							<DropdownMenuItem onClick={onView}>
								<IconEye />
								Ver agente
							</DropdownMenuItem>
							<DropdownMenuSeparator />
						</>
					)}
					<DropdownMenuItem
						disabled={!canTransition(bot.status, 'start')}
						onClick={() => run('start')}
					>
						<IconPlayerPlay />
						Iniciar
					</DropdownMenuItem>
					<DropdownMenuItem
						disabled={!canTransition(bot.status, 'pause')}
						onClick={() => run('pause')}
					>
						<IconPlayerPause />
						Pausar
					</DropdownMenuItem>
					<DropdownMenuItem
						variant="destructive"
						disabled={!canTransition(bot.status, 'stop')}
						onClick={() => setConfirmStop(true)}
					>
						<IconPlayerStop />
						Detener
					</DropdownMenuItem>
				</DropdownMenuContent>
			</DropdownMenu>

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
