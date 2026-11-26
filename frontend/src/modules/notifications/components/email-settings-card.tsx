import {
	IconAlertTriangle,
	IconLoader2,
	IconMail,
	IconSend,
} from '@tabler/icons-react';
import type { EmailSettings } from '@/modules/notifications/api/notification-settings.api';
import { ChannelStatusBadge } from '@/modules/notifications/components/channel-status-badge';
import {
	useSendEmailTestMutation,
	useUpdateEmailSettingsMutation,
} from '@/modules/notifications/hooks/use-notification-settings-mutations';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardAction,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { Checkbox } from '@/modules/ui/components/checkbox';
import {
	Field,
	FieldContent,
	FieldDescription,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { toast } from '@/modules/ui/components/toast';

type EmailSettingsCardProps = {
	settings: EmailSettings;
	/** El socio ve la configuración sin poder cambiarla. */
	readOnly: boolean;
};

export function EmailSettingsCard({
	settings,
	readOnly,
}: EmailSettingsCardProps) {
	const updateMutation = useUpdateEmailSettingsMutation();
	const testMutation = useSendEmailTestMutation();

	function handleChange(enabled: boolean) {
		updateMutation.mutate(enabled, {
			onSuccess: () =>
				toast.add({
					title: enabled ? 'Correo activado' : 'Correo desactivado',
					type: 'success',
				}),
			onError: (error) =>
				toast.add({
					title: 'No pudimos guardar el cambio',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	function handleTest() {
		testMutation.mutate(undefined, {
			onSuccess: (result) =>
				toast.add({
					title: 'Correo de prueba enviado',
					description: result.to_email
						? `Revisa la bandeja de ${result.to_email}.`
						: undefined,
					type: 'success',
				}),
			onError: (error) =>
				toast.add({
					title: 'No pudimos enviar la prueba',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Card>
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<IconMail className="size-5" />
					Correo
				</CardTitle>
				<CardDescription>
					Los mismos avisos que Telegram, al correo de cada persona. Desde el
					correo no se aprueban señales: el botón lleva a la app.
				</CardDescription>
				<CardAction>
					<ChannelStatusBadge
						active={settings.enabled && settings.smtp_configured}
						configured={settings.smtp_configured}
					/>
				</CardAction>
			</CardHeader>
			<CardContent>
				<FieldGroup>
					{!settings.smtp_configured && (
						<Alert>
							<IconAlertTriangle />
							<AlertTitle>El servidor no tiene correo configurado</AlertTitle>
							<AlertDescription>
								Mientras falten las variables SMTP en el .env del servidor, no
								sale ningún aviso por correo.
							</AlertDescription>
						</Alert>
					)}
					<Field orientation="horizontal">
						<Checkbox
							id="email-enabled"
							checked={settings.enabled}
							disabled={readOnly || updateMutation.isPending}
							onCheckedChange={(checked) => handleChange(checked)}
						/>
						<FieldContent>
							<FieldLabel htmlFor="email-enabled">
								Enviar avisos por correo
							</FieldLabel>
							<FieldDescription>
								Señales por aprobar, señales de agentes que siguen, alertas y
								avisos del fondo. El código de acceso y las invitaciones salen
								siempre.
							</FieldDescription>
						</FieldContent>
					</Field>
				</FieldGroup>
			</CardContent>
			{!readOnly && (
				<CardFooter className="justify-end">
					<Button
						type="button"
						variant="outline"
						onClick={handleTest}
						disabled={!settings.smtp_configured || testMutation.isPending}
					>
						{testMutation.isPending ? (
							<IconLoader2 className="animate-spin" />
						) : (
							<IconSend />
						)}
						Enviar prueba a mi correo
					</Button>
				</CardFooter>
			)}
		</Card>
	);
}
