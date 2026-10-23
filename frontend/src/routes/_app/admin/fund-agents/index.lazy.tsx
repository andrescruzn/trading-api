import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminFundAgentsPage } from '@/modules/fund/pages/admin-fund-agents';

export const Route = createLazyFileRoute('/_app/admin/fund-agents/')({
	component: AdminFundAgentsPage,
});
