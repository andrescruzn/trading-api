import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminFundOverviewPage } from '@/modules/fund/pages/admin-fund-overview';

export const Route = createLazyFileRoute('/_app/admin/fund')({
	component: AdminFundOverviewPage,
});
