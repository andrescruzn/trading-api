import {
	IconArrowLeft,
	IconCircleCheck,
	IconLoader2,
	IconSend,
} from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { useSendTelegramTestMutation } from '@/modules/alerts/hooks/use-alerts-mutations';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';

const ENV_EXAMPLE = `TELEGRAM_BOT_TOKEN=<token_del_bot>
TELEGRAM_DEFAULT_CHAT_ID=<id_del_chat>`;

export function AdminTelegramPage() {
	usePageBreadcrumb([
		{ label: 'Administración' },
		{ label: 'Alertas', href: '/admin/alerts' },
		{ label: 'Telegram' },
	]);
	const testMutation = useSendTelegramTestMutation();

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Canal Telegram"
				description="Comprueba que el servidor puede enviar alertas al chat de Telegram configurado."
				actions={[
					{
						label: 'Volver a alertas',
						icon: <IconArrowLeft />,
						variant: 'outline',
						render: <Link to="/admin/alerts" />,
					},
				]}
			/>
			<Card className="max-w-2xl">
				<CardHeader>
					<CardTitle>Configuración del servidor</CardTitle>
					<CardDescription>
						Estas variables van en el archivo <code className="font-mono">.env</code> del
						servidor. Después de cambiarlas, reinicia la API.
					</CardDescription>
				</CardHeader>
				<CardContent className="flex flex-col gap-4">
					<pre className="overflow-x-auto rounded-md bg-muted p-4 font-mono text-xs text-foreground">
						{ENV_EXAMPLE}
					</pre>
					<ul className="ml-4 flex list-disc flex-col gap-1 text-sm text-muted-foreground">
						<li>
							El token se obtiene al crear un bot con <strong>@BotFather</strong> en
							Telegram.
						</li>
						<li>
							El ID del chat aparece al enviarle un mensaje al bot y consultar sus
							actualizaciones en la API de Telegram.
						</li>
					</ul>

					{testMutation.isSuccess && (
						<Alert>
							<IconCircleCheck className="text-chart-1" />
							<AlertTitle>Mensaje de prueba enviado</AlertTitle>
							<AlertDescription>
								Revisa el chat de Telegram para confirmar que llegó.
							</AlertDescription>
						</Alert>
					)}
					{testMutation.isError && (
						<ErrorAlert
							title="No pudimos enviar el mensaje de prueba"
							error={testMutation.error}
						/>
					)}
				</CardContent>
				<CardFooter>
					<Button
						onClick={() => testMutation.mutate()}
						disabled={testMutation.isPending}
					>
						{testMutation.isPending ? (
							<IconLoader2 className="animate-spin" />
						) : (
							<IconSend />
						)}
						{testMutation.isPending ? 'Enviando…' : 'Enviar mensaje de prueba'}
					</Button>
				</CardFooter>
			</Card>
		</div>
	);
}
