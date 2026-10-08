import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminAlertsPage } from '@/modules/alerts/pages/admin-alerts';

export const Route = createLazyFileRoute('/_app/admin/alerts')({
	component: AdminAlertsPage,
});
