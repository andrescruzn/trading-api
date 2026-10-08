import { createLazyFileRoute } from '@tanstack/react-router';
import { IndicatorsPage } from '@/modules/features/pages/indicators';

export const Route = createLazyFileRoute('/_app/features')({
	component: IndicatorsPage,
});
