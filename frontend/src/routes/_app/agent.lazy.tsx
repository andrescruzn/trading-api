import { createLazyFileRoute } from '@tanstack/react-router';
import { AgentAnalyzePage } from '@/modules/agent/pages/analyze';

export const Route = createLazyFileRoute('/_app/agent')({
	component: AgentAnalyzePage,
});
