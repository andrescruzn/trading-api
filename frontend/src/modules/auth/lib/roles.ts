/**
 * Códigos de rol del backend (`roles.code`, ver `database/seeds/roles.py`).
 * El front decide por `role_code`, nunca por `role_id` (los IDs dependen de
 * `AUTH_*_ROLE_ID` en el `.env` del backend) ni por `role_label`.
 *
 * Fondo común: los super admin (propietarios) ven y cambian todo; el socio
 * ve lo mismo pero en solo lectura; el inversor solo lo suyo.
 */
const ROLES = {
	SUPER_ADMIN: 'super_admin',
	PARTNER: 'partner',
	INVESTOR: 'investor',
} as const;

type RoleCode = (typeof ROLES)[keyof typeof ROLES];

/** Ven la Administración y la supervisión de todo el sistema. */
const STAFF_ROLES: readonly RoleCode[] = [ROLES.SUPER_ADMIN, ROLES.PARTNER];

/** Pueden cambiar cosas: crear, editar, pausar, aprobar. */
const MANAGER_ROLES: readonly RoleCode[] = [ROLES.SUPER_ADMIN];

/** Etiquetas para mostrar un rol (la tabla de usuarios usa `role_label` de la BD). */
const ROLE_LABELS: Record<RoleCode, string> = {
	super_admin: 'Super admin',
	partner: 'Socio',
	investor: 'Inversor',
};

/**
 * Roles que un super admin puede dar al invitar o cambiar el rol. Super
 * admin no está: los propietarios se definen en el servidor.
 */
const ASSIGNABLE_ROLE_OPTIONS = (
	[ROLES.PARTNER, ROLES.INVESTOR] as RoleCode[]
).map((code) => ({ value: code, label: ROLE_LABELS[code] }));

/** Todos los roles (filtros de listados). */
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
export {
	ASSIGNABLE_ROLE_OPTIONS,
	hasAnyRole,
	hasRole,
	MANAGER_ROLES,
	ROLE_LABELS,
	ROLE_OPTIONS,
	ROLES,
	STAFF_ROLES,
};
