import { IconBrandTelegram } from '@tabler/icons-react';
import { useState } from 'react';
import { TelegramLinkDialog } from '@/modules/app-shell/components/telegram-link-dialog';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import type { SharedBot } from '@/modules/bots/api/bots.api';
import {
	BotModeBadge,
	BotStatusBadge,
} from '@/modules/bots/components/bot-badges';
import {
	useSubscribeToBotMutation,
	useUnsubscribeFromBotMutation,
} from '@/modules/bots/hooks/use-bots-mutations';
import { useSharedBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';
import { toast } from '@/modules/ui/components/toast';

const NUMERIC = 'text-right font-mono';

/**
 * Agentes de otras personas que comparten sus señales. Quien sigue uno
 * recibe por Telegram sus compras y ventas aprobadas; no se ejecuta nada en
 * su cuenta. Sin Telegram conectado no hay por dónde enviarlas, así que el
 * botón abre el diálogo para conectarlo.
 */
export function SharedAgentsSection() {
	const { user } = useAuth();
	const telegramLinked = !!user?.telegram_linked;
	const sharedQuery = useSharedBotsQuery();
	const subscribe = useSubscribeToBotMutation();
	const unsubscribe = useUnsubscribeFromBotMutation();
	const [telegramOpen, setTelegramOpen] = useState(false);

	const busyId = subscribe.isPending
		? subscribe.variables
		: unsubscribe.isPending
			? unsubscribe.variables
			: null;
	const canFollowSomeone = !!sharedQuery.data?.some((row) => !row.is_mine);

	function follow(row: SharedBot) {
		if (!telegramLinked) {
			setTelegramOpen(true);
			return;
		}
		subscribe.mutate(row.id, {
			onSuccess: () =>
				toast.add({
					title: 'Agente seguido',
					description: 'Sus señales aprobadas te llegarán por Telegram.',
					type: 'success',
				}),
			onError: (error) =>
				toast.add({
					title: 'No pudimos seguir el agente',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	function unfollow(row: SharedBot) {
		unsubscribe.mutate(row.id, {
			onSuccess: () =>
				toast.add({ title: 'Dejaste de seguirlo', type: 'success' }),
			onError: (error) =>
				toast.add({
					title: 'No pudimos dejar de seguirlo',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	const columns: DataTableColumn<SharedBot>[] = [
		{
			id: 'strategy',
			header: 'Estrategia',
			cell: (row) => (
				<span className="font-medium">{row.strategy_name ?? '—'}</span>
			),
			skeletonClassName: 'w-40',
		},
		{
			id: 'market',
			header: 'Mercado',
			cell: (row) => (
				<span className="whitespace-nowrap">
					{row.symbol ?? '—'} · {row.timeframe ?? '—'}
				</span>
			),
		},
		{
			id: 'mode',
			header: 'Modo',
			cell: (row) => <BotModeBadge mode={row.mode} />,
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => <BotStatusBadge status={row.status} />,
		},
		{
			id: 'subscribers',
			header: 'Lo siguen',
			className: NUMERIC,
			cell: (row) => row.subscribers_count,
		},
		{
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) => {
				if (row.is_mine) return <Badge variant="outline">Es tuyo</Badge>;
				const busy = busyId === row.id;
				if (row.is_subscribed) {
					return (
						<Button
							size="sm"
							variant="outline"
							disabled={busy}
							onClick={() => unfollow(row)}
						>
							Dejar de seguir
						</Button>
					);
				}
				return (
					<Button size="sm" disabled={busy} onClick={() => follow(row)}>
						{!telegramLinked && <IconBrandTelegram />}
						{telegramLinked ? 'Suscribirme' : 'Conectar Telegram'}
					</Button>
				);
			},
		},
	];

	return (
		<section className="flex flex-col gap-3">
			<div className="flex flex-col gap-1">
				<h2 className="text-base font-semibold">
					Agentes que comparten sus señales
				</h2>
				<p className="text-sm text-muted-foreground">
					Sigue un agente para recibir por Telegram sus compras y ventas
					aprobadas, con entrada, stop loss, take profit y R/R. Es solo
					información: no se abre ninguna orden en tu cuenta y no se muestra a
					quién pertenece el agente.
				</p>
			</div>
			{!telegramLinked && canFollowSomeone && (
				<Alert>
					<IconBrandTelegram />
					<AlertTitle>Conecta Telegram para seguir agentes</AlertTitle>
					<AlertDescription className="flex flex-col items-start gap-2">
						<p>
							Las señales compartidas solo llegan por Telegram. También puedes
							conectarlo desde el menú de tu usuario → Conectar Telegram.
						</p>
						<Button
							size="sm"
							variant="outline"
							onClick={() => setTelegramOpen(true)}
						>
							Conectar Telegram
						</Button>
					</AlertDescription>
				</Alert>
			)}
			<DataTable
				columns={columns}
				rows={sharedQuery.data}
				getRowId={(row) => row.id}
				isLoading={sharedQuery.isLoading}
				error={sharedQuery.error}
				errorTitle="No pudimos cargar los agentes compartidos"
				empty="Todavía ningún agente comparte sus señales. Puedes compartir las de los tuyos en su pestaña Configuración."
			/>
			<TelegramLinkDialog open={telegramOpen} onOpenChange={setTelegramOpen} />
		</section>
	);
}
