import { createFileRoute, Navigate } from '@tanstack/react-router';
import { useAuth } from '@/modules/auth/hooks/use-auth';

function IndexRedirect() {
	const { status } = useAuth();
	return <Navigate to={status === 'authenticated' ? '/dashboard' : '/login'} />;
}

export const Route = createFileRoute('/')({
	component: IndexRedirect,
});
