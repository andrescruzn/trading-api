import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminAgentsPage } from '@/modules/bots/pages/admin-agents';

export const Route = createLazyFileRoute('/_app/admin/agents')({
	component: AdminAgentsPage,
});
