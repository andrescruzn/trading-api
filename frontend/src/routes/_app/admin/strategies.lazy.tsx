import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminStrategiesPage } from '@/modules/strategies/pages/admin-strategies';

export const Route = createLazyFileRoute('/_app/admin/strategies')({
	component: AdminStrategiesPage,
});
