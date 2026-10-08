import { createLazyFileRoute } from '@tanstack/react-router';
import { InvestorDashboardPage } from '@/modules/billing/pages/investor-dashboard';

export const Route = createLazyFileRoute('/_app/investor/dashboard')({
	component: InvestorDashboardPage,
});
