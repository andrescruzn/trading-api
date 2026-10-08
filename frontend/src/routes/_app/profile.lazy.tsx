import { createLazyFileRoute } from '@tanstack/react-router';
import { ProfilePage } from '@/modules/profile/pages/profile';

export const Route = createLazyFileRoute('/_app/profile')({
	component: ProfilePage,
});
