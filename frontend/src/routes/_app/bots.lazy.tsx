import { createLazyFileRoute } from '@tanstack/react-router';
import { BotsPage } from '@/modules/bots/pages/bots';

export const Route = createLazyFileRoute('/_app/bots')({
	component: BotsPage,
});
