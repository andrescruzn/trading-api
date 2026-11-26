import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import { EmailSettingsCard } from '@/modules/notifications/components/email-settings-card';
import { TelegramSettingsCard } from '@/modules/notifications/components/telegram-settings-card';
import { useNotificationSettingsQuery } from '@/modules/notifications/hooks/use-notification-settings-queries';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { Skeleton } from '@/modules/ui/components/skeleton';

/** Canales de notificación del sistema (el socio, en solo lectura). */
export function AdminNotificationsPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Notificaciones' }]);
	const canManage = useCanManage();
	const settingsQuery = useNotificationSettingsQuery();
	const settings = settingsQuery.data;

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Notificaciones"
				description="Por dónde llegan los avisos de Trading App: Telegram y correo. Los cambios aplican al momento, sin reiniciar el servidor."
			/>
			{settingsQuery.error ? (
				<ErrorAlert
					title="No pudimos cargar las notificaciones"
					error={settingsQuery.error}
				/>
			) : !settings ? (
				<Skeleton className="h-96 w-full" />
			) : (
				<>
					<TelegramSettingsCard
						settings={settings.telegram}
						readOnly={!canManage}
					/>
					<EmailSettingsCard settings={settings.email} readOnly={!canManage} />
				</>
			)}
		</div>
	);
}
