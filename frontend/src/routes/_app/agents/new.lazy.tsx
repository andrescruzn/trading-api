import { createLazyFileRoute } from '@tanstack/react-router';
import { AgentNewPage } from '@/modules/bots/pages/agent-new';

export const Route = createLazyFileRoute('/_app/agents/new')({
	component: AgentNewPage,
});
