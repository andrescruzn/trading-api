import type { ReactNode } from 'react';
import { useHasRole } from '@/modules/auth/hooks/use-has-role';
import type { RoleCode } from '@/modules/auth/lib/roles';

type HasRoleProps = {
	role: RoleCode | readonly RoleCode[];
	children: ReactNode;
	fallback?: ReactNode;
};

export function HasRole({ role, children, fallback }: HasRoleProps) {
	const allowed = useHasRole(role);
	return allowed ? children : (fallback ?? null);
}
