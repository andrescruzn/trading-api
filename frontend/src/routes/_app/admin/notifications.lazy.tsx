import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminNotificationsPage } from '@/modules/notifications/pages/admin-notifications';

export const Route = createLazyFileRoute('/_app/admin/notifications')({
	component: AdminNotificationsPage,
});
