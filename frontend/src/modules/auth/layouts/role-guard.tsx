import { Navigate, Outlet } from '@tanstack/react-router';
import type { ReactNode } from 'react';
import { useHasRole } from '@/modules/auth/hooks/use-has-role';
import {
	MANAGER_ROLES,
	type RoleCode,
	STAFF_ROLES,
} from '@/modules/auth/lib/roles';

/**
 * Guard de rol para un grupo de rutas. Va dentro del shell autenticado
 * (`_app`), así que aquí ya hay sesión: si el rol no alcanza, vuelve al inicio.
 * Es solo UX — el backend valida el rol en cada endpoint.
 */
function RoleGuard({ role }: { role: RoleCode | readonly RoleCode[] }) {
	const allowed = useHasRole(role);
	return allowed ? <Outlet /> : <Navigate to="/dashboard" />;
}

/** Administración: super admin y socio (el socio, en solo lectura). */
function AdminGuardLayout() {
	return <RoleGuard role={STAFF_ROLES} />;
}

/**
 * Página suelta que solo usa quien cambia cosas (p. ej. crear un agente).
 * Para el socio y el inversor, vuelve al inicio.
 */
function ManagerGuard({ children }: { children: ReactNode }) {
	const allowed = useHasRole(MANAGER_ROLES);
	return allowed ? children : <Navigate to="/dashboard" />;
}

export { AdminGuardLayout, ManagerGuard };
