import type { TablerIcon } from '@tabler/icons-react';
import type { RoleCode } from '@/modules/auth/lib/roles';

/**
 * Un rol o una lista de roles: basta con tener cualquiera para ver el ítem.
 * Sin `role`, el ítem lo ve cualquier usuario autenticado.
 */
export type NavRole = RoleCode | readonly RoleCode[];

export type NavSubItem = {
	title: string;
	url: string;
	role?: NavRole;
};

export type NavItem = {
	title: string;
	url?: string;
	/** Rutas extra que también marcan el ítem como activo (pantallas que cuelgan de él). */
	activePaths?: string[];
	icon?: TablerIcon;
	role?: NavRole;
	items?: NavSubItem[];
};

export type NavSectionData = {
	label: string;
	/** Rol requerido para ver la sección completa (además del de cada ítem). */
	role?: NavRole;
	items: NavItem[];
};
