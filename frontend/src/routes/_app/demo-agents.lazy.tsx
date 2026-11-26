import { createLazyFileRoute } from '@tanstack/react-router';
import { StaffGuard } from '@/modules/auth/layouts/role-guard';
import { DemoAgentsPage } from '@/modules/bots/pages/demo-agents';

export const Route = createLazyFileRoute('/_app/demo-agents')({
	component: () => (
		<StaffGuard>
			<DemoAgentsPage />
		</StaffGuard>
	),
});
