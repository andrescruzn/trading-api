import { createFileRoute } from '@tanstack/react-router';
import { AuthLayout } from '@/modules/auth/layouts/auth';

export const Route = createFileRoute('/_auth')({
	component: AuthLayout,
});
