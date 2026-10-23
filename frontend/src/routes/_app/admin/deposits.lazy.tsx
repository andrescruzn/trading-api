import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminDepositsPage } from '@/modules/fund/pages/admin-deposits';

export const Route = createLazyFileRoute('/_app/admin/deposits')({
	component: AdminDepositsPage,
});
