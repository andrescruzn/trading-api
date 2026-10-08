import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminManagedAccountsPage } from '@/modules/billing/pages/admin-managed-accounts';

export const Route = createLazyFileRoute('/_app/admin/managed-accounts')({
	component: AdminManagedAccountsPage,
});
