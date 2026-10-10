import { createLazyFileRoute } from '@tanstack/react-router';
import { AgentDetailPage } from '@/modules/bots/pages/agent-detail';

export const Route = createLazyFileRoute('/_app/agents/$agentId')({
	component: AgentDetailPage,
});
