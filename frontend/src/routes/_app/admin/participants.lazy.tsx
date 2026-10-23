import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminParticipantsPage } from '@/modules/fund/pages/admin-participants';

export const Route = createLazyFileRoute('/_app/admin/participants')({
	component: AdminParticipantsPage,
});
