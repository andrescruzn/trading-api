import { createLazyFileRoute } from '@tanstack/react-router';
import { AgentsPage } from '@/modules/bots/pages/agents';

export const Route = createLazyFileRoute('/_app/agents/')({
	component: AgentsPage,
});
