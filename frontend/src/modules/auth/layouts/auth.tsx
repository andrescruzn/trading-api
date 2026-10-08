import { Navigate, Outlet } from '@tanstack/react-router';
import { useAuth } from '@/modules/auth/hooks/use-auth';

export function AuthLayout() {
	const { status } = useAuth();

	if (status === 'authenticated') {
		return <Navigate to="/dashboard" />;
	}

	return <Outlet />;
}
