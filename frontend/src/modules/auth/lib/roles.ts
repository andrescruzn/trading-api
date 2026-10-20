/**
 * Códigos de rol del backend (`roles.code`, ver `database/seeds/roles.py`).
 * El front decide por `role_code`, nunca por `role_id` (los IDs dependen de
 * `AUTH_*_ROLE_ID` en el `.env` del backend) ni por `role_label`.
 */
const ROLES = {
	USER: 'user',
	ADMIN: 'admin',
	INVESTOR: 'investor',
} as const;

type RoleCode = (typeof ROLES)[keyof typeof ROLES];

/** Etiquetas para elegir un rol (la tabla muestra `role_label` de la BD). */
const ROLE_LABELS: Record<RoleCode, string> = {
	user: 'Usuario',
	admin: 'Administrador',
	investor: 'Inversor',
};

const ROLE_OPTIONS = (Object.keys(ROLE_LABELS) as RoleCode[]).map((code) => ({
	value: code,
	label: ROLE_LABELS[code],
}));

type WithRole = { role_code: string | null };

function hasRole(user: WithRole, role: RoleCode): boolean {
	return user.role_code === role;
}

function hasAnyRole(user: WithRole, roles: readonly RoleCode[]): boolean {
	return roles.some((role) => hasRole(user, role));
}

export type { RoleCode };
export { hasAnyRole, hasRole, ROLE_LABELS, ROLE_OPTIONS, ROLES };
