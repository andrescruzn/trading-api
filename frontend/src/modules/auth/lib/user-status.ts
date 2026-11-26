import type { UserSummary } from '@/modules/auth/api/users.api';

/**
 * Estado de la cuenta (`users.status`, CHECK `active | blocked | disabled`).
 * Bloqueado y Desactivado impiden entrar por igual; cambia el motivo:
 * bloquear es una suspensión temporal y desactivar, una cuenta que ya no se usa.
 */
const USER_STATUSES = {
	ACTIVE: 'active',
	BLOCKED: 'blocked',
	DISABLED: 'disabled',
} as const;

type UserStatus = (typeof USER_STATUSES)[keyof typeof USER_STATUSES];

/** Cambio pedido desde la tabla de Usuarios (diálogo de confirmación). */
type UserStatusChange = { user: UserSummary; status: UserStatus };

const USER_STATUS_LABELS: Record<UserStatus, string> = {
	active: 'Activo',
	blocked: 'Bloqueado',
	disabled: 'Desactivado',
};

/** Acción del menú para llevar la cuenta a cada estado. */
const USER_STATUS_ACTION_LABELS: Record<UserStatus, string> = {
	active: 'Activar cuenta',
	blocked: 'Bloquear cuenta',
	disabled: 'Desactivar cuenta',
};

function userStatusLabel(status: string): string {
	return USER_STATUS_LABELS[status as UserStatus] ?? status;
}

export type { UserStatus, UserStatusChange };
export {
	USER_STATUS_ACTION_LABELS,
	USER_STATUS_LABELS,
	USER_STATUSES,
	userStatusLabel,
};
