import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminUsersPage } from '@/modules/auth/pages/admin-users';

export const Route = createLazyFileRoute('/_app/admin/users')({
	component: AdminUsersPage,
});
