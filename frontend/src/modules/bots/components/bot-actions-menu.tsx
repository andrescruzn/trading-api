import {
	IconBolt,
	IconDots,
	IconLoader2,
	IconPlayerPause,
	IconPlayerPlay,
	IconPlayerStop,
} from '@tabler/icons-react';
import { useState } from 'react';
import type { Bot, BotTransition } from '@/modules/bots/api/bots.api';
import { useTransitionBotMutation } from '@/modules/bots/hooks/use-bots-mutations';
import { canTransition } from '@/modules/bots/lib/bots-labels';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from '@/modules/ui/components/alert-dialog';
import { Button } from '@/modules/ui/components/button';
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from '@/modules/ui/components/dropdown-menu';
import { toast } from '@/modules/ui/components/toast';

const TRANSITION_COPY: Record<
	BotTransition,
	{ success: string; error: string }
> = {
	start: { success: 'Bot iniciado', error: 'No pudimos iniciar el bot' },
	pause: { success: 'Bot pausado', error: 'No pudimos pausar el bot' },
	stop: { success: 'Bot detenido', error: 'No pudimos detener el bot' },
};

type BotActionsMenuProps = {
	bot: Bot;
	/** Si se pasa, el menú incluye "Ver señales". */
	onViewSignals?: () => void;
};

/**
 * Menú de acciones de una fila de bot: iniciar, pausar y detener (con
 * confirmación). Las transiciones que el estado actual no permite quedan
 * deshabilitadas.
 */
export function BotActionsMenu({ bot, onViewSignals }: BotActionsMenuProps) {
	const transitionMutation = useTransitionBotMutation();
	const [confirmStop, setConfirmStop] = useState(false);
	const isPending = transitionMutation.isPending;

	function runTransition(transition: BotTransition, onDone?: () => void) {
		transitionMutation.mutate(
			{ id: bot.id, transition },
			{
				onSuccess: () => {
					toast.add({
						title: TRANSITION_COPY[transition].success,
						type: 'success',
					});
					onDone?.();
				},
				onError: (error) =>
					toast.add({
						title: TRANSITION_COPY[transition].error,
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

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
					<span className="sr-only">Acciones del bot #{bot.id}</span>
				</DropdownMenuTrigger>
				<DropdownMenuContent align="end" className="w-auto min-w-44">
					{onViewSignals && (
						<>
							<DropdownMenuItem onClick={onViewSignals}>
								<IconBolt />
								Ver señales
							</DropdownMenuItem>
							<DropdownMenuSeparator />
						</>
					)}
					<DropdownMenuItem
						disabled={!canTransition(bot.status, 'start')}
						onClick={() => runTransition('start')}
					>
						<IconPlayerPlay />
						Iniciar
					</DropdownMenuItem>
					<DropdownMenuItem
						disabled={!canTransition(bot.status, 'pause')}
						onClick={() => runTransition('pause')}
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

			<AlertDialog open={confirmStop} onOpenChange={setConfirmStop}>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>¿Detener el bot #{bot.id}?</AlertDialogTitle>
						<AlertDialogDescription>
							El bot deja de generar señales. Las posiciones abiertas no se
							cierran.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel>Cancelar</AlertDialogCancel>
						<AlertDialogAction
							variant="destructive"
							disabled={isPending}
							onClick={() => runTransition('stop', () => setConfirmStop(false))}
						>
							{isPending && <IconLoader2 className="animate-spin" />}
							Detener bot
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</div>
	);
}
