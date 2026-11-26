import { createLazyFileRoute } from '@tanstack/react-router';
import { ManagerGuard } from '@/modules/auth/layouts/role-guard';
import { AgentNewPage } from '@/modules/bots/pages/agent-new';

export const Route = createLazyFileRoute('/_app/agents/new')({
	component: () => (
		<ManagerGuard>
			<AgentNewPage />
		</ManagerGuard>
	),
});
