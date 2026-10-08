import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminExchangesPage } from '@/modules/market/pages/admin-exchanges';

export const Route = createLazyFileRoute('/_app/admin/exchanges')({
	component: AdminExchangesPage,
});
