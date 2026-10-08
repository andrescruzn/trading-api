import { createLazyFileRoute } from '@tanstack/react-router';
import { StrategiesPage } from '@/modules/strategies/pages/strategies';

export const Route = createLazyFileRoute('/_app/strategies')({
	component: StrategiesPage,
});
