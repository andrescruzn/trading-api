import { createLazyFileRoute } from '@tanstack/react-router';
import { DashboardPage } from '@/modules/dashboard/pages/dashboard';

export const Route = createLazyFileRoute('/_app/dashboard')({
	component: DashboardPage,
});
