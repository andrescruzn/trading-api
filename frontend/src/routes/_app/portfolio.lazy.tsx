import { createLazyFileRoute } from '@tanstack/react-router';
import { PortfolioPage } from '@/modules/accounts/pages/portfolio';
import { ManagerGuard } from '@/modules/auth/layouts/role-guard';

export const Route = createLazyFileRoute('/_app/portfolio')({
	component: () => (
		<ManagerGuard>
			<PortfolioPage />
		</ManagerGuard>
	),
});
