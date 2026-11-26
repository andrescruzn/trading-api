import { createFileRoute } from '@tanstack/react-router';
import { AdminGuardLayout } from '@/modules/auth/layouts/role-guard';

export const Route = createFileRoute('/_app/admin')({
	component: AdminGuardLayout,
});
