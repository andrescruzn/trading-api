import { useState } from 'react';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import type { Bot, BotExecutionMode } from '@/modules/bots/api/bots.api';
import { ApprovalTtlField } from '@/modules/bots/components/approval-ttl-field';
import { ExecutionModePicker } from '@/modules/bots/components/execution-mode-picker';
import { useUpdateBotMutation } from '@/modules/bots/hooks/use-bots-mutations';
import { EXECUTION_MODE_LABELS } from '@/modules/bots/lib/bots-labels';
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
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { toast } from '@/modules/ui/components/toast';

/**
 * Cambia el modo de ejecución del agente. Se puede en cualquier estado:
 * pasar de Automático a Con aprobación es un freno que no debe esperar a
 * detener el agente.
 */
export function ExecutionModeCard({ bot }: { bot: Bot }) {
	// El socio ve el modo pero no lo cambia.
	const canManage = useCanManage();
	const mutation = useUpdateBotMutation();
	const [pendingAuto, setPendingAuto] = useState(false);

	function save(mode: BotExecutionMode) {
		mutation.mutate(
			{ id: bot.id, input: { execution_mode: mode } },
			{
				onSuccess: () => {
					setPendingAuto(false);
					toast.add({
						title: `Modo: ${EXECUTION_MODE_LABELS[mode]}`,
						type: 'success',
					});
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos cambiar el modo',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	function handleChange(mode: BotExecutionMode) {
		if (mode === bot.execution_mode) return;
		// Automático envía órdenes sin preguntar: se confirma siempre
		if (mode === 'auto') {
			setPendingAuto(true);
			return;
		}
		save(mode);
	}

	return (
		<Card className="lg:col-span-2">
			<CardHeader>
				<CardTitle>Cuando la IA aprueba una operación</CardTitle>
				<CardDescription>
					En los modos automáticos el agente analiza cada vela cerrada del
					timeframe. Toda orden pasa por la regla del 1 %, el riesgo/beneficio
					mínimo de 2:1 y los límites del servidor.
				</CardDescription>
			</CardHeader>
			<CardContent className="flex flex-col gap-6">
				<ExecutionModePicker
					value={bot.execution_mode}
					onChange={handleChange}
					accountMode={bot.mode}
					disabled={mutation.isPending || !canManage}
				/>
				{bot.execution_mode === 'approval' && canManage && (
					<ApprovalTtlField
						key={bot.approval_ttl_minutes ?? 'default'}
						bot={bot}
					/>
				)}
			</CardContent>

			<AlertDialog open={pendingAuto} onOpenChange={setPendingAuto}>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>¿Activar el modo Automático?</AlertDialogTitle>
						<AlertDialogDescription>
							{bot.mode === 'live'
								? 'El agente enviará órdenes con dinero real sin pedirte confirmación. '
								: 'El agente enviará órdenes con dinero simulado sin pedirte confirmación. '}
							Cada posición se cierra sola al tocar su stop loss o su take
							profit. Puedes volver a Con aprobación en cualquier momento.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel>Cancelar</AlertDialogCancel>
						<AlertDialogAction
							variant={bot.mode === 'live' ? 'destructive' : 'default'}
							disabled={mutation.isPending}
							onClick={() => save('auto')}
						>
							Activar Automático
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</Card>
	);
}
