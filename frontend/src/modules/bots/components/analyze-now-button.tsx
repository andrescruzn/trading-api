import { IconLoader2, IconSparkles } from '@tabler/icons-react';
import type { Bot, Signal } from '@/modules/bots/api/bots.api';
import { useGenerateSignalMutation } from '@/modules/bots/hooks/use-bots-mutations';
import {
	rejectionLabel,
	SIGNAL_ACTION_LABELS,
} from '@/modules/bots/lib/bots-labels';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button } from '@/modules/ui/components/button';
import { toast } from '@/modules/ui/components/toast';

type AnalyzeNowButtonProps = {
	bot: Bot;
	/** Recibe la señal generada (p. ej. para abrir su detalle). */
	onResult?: (signal: Signal) => void;
	size?: 'xs' | 'sm' | 'default';
};

/**
 * Pide a la IA que evalúe el mercado ahora mismo con la estrategia del
 * agente. El resultado se guarda como señal (aprobada o rechazada).
 */
export function AnalyzeNowButton({
	bot,
	onResult,
	size = 'sm',
}: AnalyzeNowButtonProps) {
	const mutation = useGenerateSignalMutation();
	const isRunning = bot.status === 'running';

	function handleClick() {
		mutation.mutate(bot.id, {
			onSuccess: (signal) => {
				toast.add({
					title: 'Análisis listo',
					description: signal.approved
						? `${SIGNAL_ACTION_LABELS[signal.action]}: pasó todos los filtros.`
						: (rejectionLabel(signal.reasons?.rejection_reason) ??
							'La operación no pasó los filtros.'),
					type: signal.approved ? 'success' : 'info',
				});
				onResult?.(signal);
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos analizar el mercado',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Button
			size={size}
			variant="outline"
			onClick={handleClick}
			disabled={!isRunning || mutation.isPending}
			title={isRunning ? undefined : 'Inicia el agente para analizar'}
		>
			{mutation.isPending ? (
				<IconLoader2 className="animate-spin" />
			) : (
				<IconSparkles />
			)}
			{mutation.isPending ? 'Analizando…' : 'Analizar ahora'}
		</Button>
	);
}
