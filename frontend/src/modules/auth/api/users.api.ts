import type { RoleCode } from '@/modules/auth/lib/roles';
import { api } from '@/modules/shared/lib/api-client';

/** `GET /users` (solo admin): identificación de cada usuario. */
type UserSummary = {
	id: number;
	email: string;
	full_name: string | null;
	role_code: RoleCode | null;
	role_label: string | null;
	status: string;
};

function listUsers() {
	return api.get<UserSummary[]>('/users');
}

export type { UserSummary };
export { listUsers };
