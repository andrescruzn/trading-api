import { createLazyFileRoute } from '@tanstack/react-router';
import { AlertsPage } from '@/modules/alerts/pages/alerts';

export const Route = createLazyFileRoute('/_app/alerts')({
	component: AlertsPage,
});
