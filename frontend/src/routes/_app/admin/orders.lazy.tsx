import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminOrdersPage } from '@/modules/orders/pages/admin-orders';

export const Route = createLazyFileRoute('/_app/admin/orders')({
	component: AdminOrdersPage,
});
