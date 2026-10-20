import { createLazyFileRoute } from '@tanstack/react-router';
import { BacktestPage } from '@/modules/strategies/pages/backtest';

export const Route = createLazyFileRoute('/_app/backtest')({
	component: BacktestPage,
});
