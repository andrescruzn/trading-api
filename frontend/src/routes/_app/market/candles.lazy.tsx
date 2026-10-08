import { createLazyFileRoute } from '@tanstack/react-router';
import { CandlesPage } from '@/modules/market/pages/candles';

export const Route = createLazyFileRoute('/_app/market/candles')({
	component: CandlesPage,
});
