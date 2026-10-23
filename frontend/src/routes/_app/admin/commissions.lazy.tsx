import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminCommissionsPage } from '@/modules/fund/pages/admin-commissions';

export const Route = createLazyFileRoute('/_app/admin/commissions')({
	component: AdminCommissionsPage,
});
