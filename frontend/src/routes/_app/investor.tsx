import { createFileRoute } from '@tanstack/react-router';
import { InvestorGuardLayout } from '@/modules/auth/layouts/role-guard';

export const Route = createFileRoute('/_app/investor')({
	component: InvestorGuardLayout,
});
