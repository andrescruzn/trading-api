import { Navigate, Outlet } from '@tanstack/react-router';
import { useHasRole } from '@/modules/auth/hooks/use-has-role';
import { ROLES, type RoleCode } from '@/modules/auth/lib/roles';

/**
 * Guard de rol para un grupo de rutas. Va dentro del shell autenticado
 * (`_app`), así que aquí ya hay sesión: si el rol no alcanza, vuelve al inicio.
 * Es solo UX — el backend valida el rol en cada endpoint.
 */
function RoleGuard({ role }: { role: RoleCode }) {
	const allowed = useHasRole(role);
	return allowed ? <Outlet /> : <Navigate to="/dashboard" />;
}

function AdminGuardLayout() {
	return <RoleGuard role={ROLES.ADMIN} />;
}

function InvestorGuardLayout() {
	return <RoleGuard role={ROLES.INVESTOR} />;
}

export { AdminGuardLayout, InvestorGuardLayout };
