import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminAccountsPage } from '@/modules/accounts/pages/admin-accounts';

export const Route = createLazyFileRoute('/_app/admin/accounts')({
	component: AdminAccountsPage,
});
