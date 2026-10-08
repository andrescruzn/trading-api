import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminCandlesIngestPage } from '@/modules/market/pages/admin-candles-ingest';

export const Route = createLazyFileRoute('/_app/admin/candles/ingest')({
	component: AdminCandlesIngestPage,
});
