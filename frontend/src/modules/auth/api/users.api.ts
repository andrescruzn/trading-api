import type { RoleCode } from '@/modules/auth/lib/roles';
import { api } from '@/modules/shared/lib/api-client';

/** `GET /users` (solo admin): identificación de cada usuario. */
type UserSummary = {
	id: number;
	email: string;
	full_name: string | null;
	role_code: RoleCode | null;
	role_label: string | null;
	/** `active` | `blocked` | `disabled`. */
	status: string;
	last_login_at: string | null;
};

function listUsers() {
	return api.get<UserSummary[]>('/users');
}

/** Solo admin y nunca sobre uno mismo (el backend responde 422). */
function updateUserRole(id: number, roleCode: RoleCode) {
	return api.put<UserSummary>(`/users/${id}/role`, { role_code: roleCode });
}

export type { UserSummary };
export { listUsers, updateUserRole };
