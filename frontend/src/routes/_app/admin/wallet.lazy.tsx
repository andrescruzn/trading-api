import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminWalletPage } from '@/modules/accounts/pages/admin-wallet';

export const Route = createLazyFileRoute('/_app/admin/wallet')({
	component: AdminWalletPage,
});
