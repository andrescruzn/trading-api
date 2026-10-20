import type { RoleCode } from '@/modules/auth/lib/roles';
import type { UserStatus } from '@/modules/auth/lib/user-status';
import { api } from '@/modules/shared/lib/api-client';

/** `GET /users` (solo admin): identificación de cada usuario. */
type UserSummary = {
	id: number;
	email: string;
	full_name: string | null;
	role_code: RoleCode | null;
	role_label: string | null;
	status: UserStatus;
	last_login_at: string | null;
};

function listUsers() {
	return api.get<UserSummary[]>('/users');
}

type InviteUserInput = {
	email: string;
	full_name: string | null;
	role_code: RoleCode;
};

/** Solo admin: crea la cuenta y envía el correo de bienvenida. */
function inviteUser(input: InviteUserInput) {
	return api.post<UserSummary>('/users', input);
}

/** Solo admin y nunca sobre uno mismo (el backend responde 422). */
function updateUserRole(id: number, roleCode: RoleCode) {
	return api.put<UserSummary>(`/users/${id}/role`, { role_code: roleCode });
}

/**
 * Solo admin y nunca sobre uno mismo (422). Bloquear o desactivar cierra la
 * sesión de la persona al instante.
 */
function updateUserStatus(id: number, status: UserStatus) {
	return api.put<UserSummary>(`/users/${id}/status`, { status });
}

export type { InviteUserInput, UserSummary };
export { inviteUser, listUsers, updateUserRole, updateUserStatus };
