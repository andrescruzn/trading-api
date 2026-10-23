import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import type { Bot } from '@/modules/bots/api/bots.api';
import { useUpdateBotMutation } from '@/modules/bots/hooks/use-bots-mutations';
import { useSharedBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { Checkbox } from '@/modules/ui/components/checkbox';
import {
	Field,
	FieldDescription,
	FieldLabel,
} from '@/modules/ui/components/field';
import { toast } from '@/modules/ui/components/toast';

function subscribersText(count: number) {
	if (count === 0) return 'Todavía nadie sigue este agente.';
	if (count === 1) return '1 persona sigue este agente.';
	return `${count} personas siguen este agente.`;
}

/**
 * Activa "Compartir señales": otros usuarios pueden seguir el agente y
 * recibir por Telegram sus compras y ventas aprobadas. Se cambia en
 * cualquier estado. Al apagarlo las suscripciones se conservan, pero no se
 * envía nada hasta que se vuelva a compartir.
 */
export function ShareSignalsCard({ bot }: { bot: Bot }) {
	// El socio ve si se comparte pero no lo cambia.
	const canManage = useCanManage();
	const mutation = useUpdateBotMutation();
	// El conteo sale del listado público, que incluye los agentes propios
	const sharedQuery = useSharedBotsQuery({ enabled: bot.share_signals });
	const subscribers = sharedQuery.data?.find(
		(item) => item.id === bot.id,
	)?.subscribers_count;

	function handleChange(checked: boolean) {
		mutation.mutate(
			{ id: bot.id, input: { share_signals: checked } },
			{
				onSuccess: () =>
					toast.add({
						title: checked ? 'Señales compartidas' : 'Dejaste de compartir',
						type: 'success',
					}),
				onError: (error) =>
					toast.add({
						title: 'No pudimos guardar el cambio',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Card className="lg:col-span-2">
			<CardHeader>
				<CardTitle>Compartir señales</CardTitle>
				<CardDescription>
					Otras personas de Trading App podrán seguir este agente y recibir por
					Telegram sus compras y ventas aprobadas: símbolo, entrada, stop loss,
					take profit y R/R. No verán tu cuenta, tus montos ni el nombre del
					agente, y en sus cuentas no se ejecuta nada.
				</CardDescription>
			</CardHeader>
			<CardContent>
				<Field orientation="horizontal">
					<Checkbox
						id={`agent-share-signals-${bot.id}`}
						checked={bot.share_signals}
						disabled={mutation.isPending || !canManage}
						onCheckedChange={(checked) => handleChange(checked)}
					/>
					<div className="flex flex-col gap-0.5">
						<FieldLabel htmlFor={`agent-share-signals-${bot.id}`}>
							Compartir las señales de este agente
						</FieldLabel>
						<FieldDescription>
							{bot.share_signals
								? subscribers !== undefined
									? subscribersText(subscribers)
									: 'Aparece en Track record para que otros lo sigan.'
								: 'Si lo apagas, nadie recibe sus señales; quienes lo seguían vuelven a recibirlas si lo compartes otra vez.'}
						</FieldDescription>
					</div>
				</Field>
			</CardContent>
		</Card>
	);
}
