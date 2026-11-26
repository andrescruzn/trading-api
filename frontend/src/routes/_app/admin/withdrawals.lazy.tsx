import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminWithdrawalsPage } from '@/modules/fund/pages/admin-withdrawals';

export const Route = createLazyFileRoute('/_app/admin/withdrawals')({
	component: AdminWithdrawalsPage,
});
