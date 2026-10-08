import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminInvestorsPage } from '@/modules/billing/pages/admin-investors';

export const Route = createLazyFileRoute('/_app/admin/investors')({
	component: AdminInvestorsPage,
});
