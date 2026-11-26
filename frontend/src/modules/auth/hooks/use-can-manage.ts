import { useHasRole } from '@/modules/auth/hooks/use-has-role';
import { MANAGER_ROLES } from '@/modules/auth/lib/roles';

/**
 * True si la persona puede cambiar cosas (crear, editar, pausar, aprobar).
 * Hoy solo el super admin: el socio ve lo mismo en solo lectura. Las
 * acciones de escritura se ocultan con esto; el backend igual responde 403.
 */
function useCanManage(): boolean {
	return useHasRole(MANAGER_ROLES);
}

export { useCanManage };
