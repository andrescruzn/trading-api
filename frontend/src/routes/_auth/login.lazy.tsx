import { createLazyFileRoute } from '@tanstack/react-router';
import { LoginPage } from '@/modules/auth/pages/login';

export const Route = createLazyFileRoute('/_auth/login')({
	component: LoginPage,
});
