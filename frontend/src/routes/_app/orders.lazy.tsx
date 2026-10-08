import { createLazyFileRoute } from '@tanstack/react-router';
import { OrdersPage } from '@/modules/orders/pages/orders';

export const Route = createLazyFileRoute('/_app/orders')({
	component: OrdersPage,
});
