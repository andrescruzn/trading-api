import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminCandlesPage } from '@/modules/market/pages/admin-candles';

export const Route = createLazyFileRoute('/_app/admin/candles/view')({
	component: AdminCandlesPage,
});
