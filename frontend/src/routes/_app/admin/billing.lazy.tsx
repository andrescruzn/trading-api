import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminBillingPage } from '@/modules/billing/pages/admin-billing';

export const Route = createLazyFileRoute('/_app/admin/billing')({
	component: AdminBillingPage,
});
