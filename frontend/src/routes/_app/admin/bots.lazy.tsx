import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminBotsPage } from '@/modules/bots/pages/admin-bots';

export const Route = createLazyFileRoute('/_app/admin/bots')({
	component: AdminBotsPage,
});
