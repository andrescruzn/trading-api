import type { Bot, BotTransition } from '@/modules/bots/api/bots.api';
import { useTransitionBotMutation } from '@/modules/bots/hooks/use-bots-mutations';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { toast } from '@/modules/ui/components/toast';

const TRANSITION_COPY: Record<
	BotTransition,
	{ success: string; error: string }
> = {
	start: { success: 'Agente iniciado', error: 'No pudimos iniciar el agente' },
	pause: { success: 'Agente pausado', error: 'No pudimos pausar el agente' },
	stop: { success: 'Agente detenido', error: 'No pudimos detener el agente' },
};

/**
 * Iniciar, pausar o detener un agente con sus toasts. Lo comparten el menú
 * de la tabla, las tarjetas y la cabecera del detalle.
 */
function useBotTransition(bot: Pick<Bot, 'id'>) {
	const mutation = useTransitionBotMutation();

	function run(transition: BotTransition, onDone?: () => void) {
		mutation.mutate(
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

	return {
		run,
		isPending: mutation.isPending,
		/** Transición en curso, para mostrar el spinner en su botón. */
		pendingTransition: mutation.isPending
			? mutation.variables?.transition
			: undefined,
	};
}

export { useBotTransition };
