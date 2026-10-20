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
	read: 'Solo consultas',
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

/** Fecha con segundos (en auditoría importa el orden exacto), hora local. */
function formatAuditTime(iso: string): string {
	const date = new Date(iso);
	if (Number.isNaN(date.getTime())) return '—';
	return date.toLocaleString('es-CO', {
		dateStyle: 'medium',
		timeStyle: 'medium',
	});
}

/** `YYYY-MM-DD` del `<input type="date">` → inicio de ese día local en ISO. */
function startOfLocalDayIso(day: string): string {
	return new Date(`${day}T00:00:00`).toISOString();
}

/** Fin exclusivo del rango: inicio del día local siguiente en ISO. */
function startOfNextLocalDayIso(day: string): string {
	const date = new Date(`${day}T00:00:00`);
	date.setDate(date.getDate() + 1);
	return date.toISOString();
}

export {
	AUDIT_EVENT_TYPE_LABELS,
	AUDIT_EVENT_TYPE_OPTIONS,
	AUDIT_KIND_LABELS,
	AUDIT_KIND_OPTIONS,
	auditEventTypeLabel,
	formatAuditTime,
	httpMethodLabel,
	isErrorStatus,
	startOfLocalDayIso,
	startOfNextLocalDayIso,
};
