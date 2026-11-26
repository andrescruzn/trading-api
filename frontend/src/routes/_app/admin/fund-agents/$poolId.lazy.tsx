import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminFundAgentDetailPage } from '@/modules/fund/pages/admin-fund-agent-detail';

export const Route = createLazyFileRoute('/_app/admin/fund-agents/$poolId')({
	component: AdminFundAgentDetailPage,
});
