import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminTimeframesPage } from '@/modules/market/pages/admin-timeframes';

export const Route = createLazyFileRoute('/_app/admin/timeframes')({
	component: AdminTimeframesPage,
});
