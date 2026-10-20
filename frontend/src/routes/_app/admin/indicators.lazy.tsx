import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminIndicatorsPage } from '@/modules/features/pages/admin-indicators';

export const Route = createLazyFileRoute('/_app/admin/indicators')({
	component: AdminIndicatorsPage,
});
