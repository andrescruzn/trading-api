import type { AuditEventType, AuditKind } from '@/modules/auth/api/audit.api';
import type { SelectOption } from '@/modules/shared/components/option-select';

const AUDIT_EVENT_TYPE_LABELS: Record<AuditEventType, string> = {
	LOGIN_OTP_REQUEST: 'Pidió un código de entrada',
	VERIFY_OTP: 'Escribió el código de entrada',
	LOGOUT: 'Cerró sesión',
	GET_PROFILE: 'Consultó su perfil',
	ROTATE_TOKEN: 'Renovó la sesión',
	HTTP_REQUEST: 'Otra acción en la app',
};

const AUDIT_EVENT_TYPE_OPTIONS: SelectOption[] = (
	Object.keys(AUDIT_EVENT_TYPE_LABELS) as AuditEventType[]
).map((value) => ({ value, label: AUDIT_EVENT_TYPE_LABELS[value] }));

const AUDIT_KIND_LABELS: Record<AuditKind, string> = {
	write: 'Solo cambios',
	// Las consultas que salen bien no se guardan: solo quedan las fallidas.
	read: 'Solo consultas con error',
};

const AUDIT_KIND_OPTIONS: SelectOption[] = (
	Object.keys(AUDIT_KIND_LABELS) as AuditKind[]
).map((value) => ({ value, label: AUDIT_KIND_LABELS[value] }));

/** Qué hace cada método HTTP, en palabras de la persona. */
const HTTP_METHOD_LABELS: Record<string, string> = {
	GET: 'Consulta',
	HEAD: 'Consulta',
	OPTIONS: 'Consulta',
	POST: 'Crea o ejecuta',
	PUT: 'Modifica',
	PATCH: 'Modifica',
	DELETE: 'Elimina',
};

function auditEventTypeLabel(eventType: string): string {
	return AUDIT_EVENT_TYPE_LABELS[eventType as AuditEventType] ?? eventType;
}

function httpMethodLabel(method: string): string {
	return HTTP_METHOD_LABELS[method] ?? method;
}

function isErrorStatus(status: number): boolean {
	return status >= 400;
}

export {
	AUDIT_EVENT_TYPE_LABELS,
	AUDIT_EVENT_TYPE_OPTIONS,
	AUDIT_KIND_LABELS,
	AUDIT_KIND_OPTIONS,
	auditEventTypeLabel,
	httpMethodLabel,
	isErrorStatus,
};
