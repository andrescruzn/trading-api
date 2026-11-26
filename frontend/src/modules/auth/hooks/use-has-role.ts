import { useAuth } from '@/modules/auth/hooks/use-auth';
import { hasAnyRole, type RoleCode } from '@/modules/auth/lib/roles';

function useHasRole(role: RoleCode | readonly RoleCode[]): boolean {
	const { user } = useAuth();
	if (!user) return false;
	return hasAnyRole(user, typeof role === 'string' ? [role] : role);
}

export { useHasRole };
