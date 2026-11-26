import { api } from '@/modules/shared/lib/api-client';
import type { Paginated } from '@/modules/shared/types/api';

/** `event_type` que resuelve el middleware de auditoría del backend. */
type AuditEventType =
	| 'LOGIN_OTP_REQUEST'
	| 'VERIFY_OTP'
	| 'LOGOUT'
	| 'GET_PROFILE'
	| 'ROTATE_TOKEN'
	| 'HTTP_REQUEST';

/** `GET /audit-logs` (solo admin). Sin payloads: solo lo útil para auditar. */
type AuditEvent = {
	/** `<año>-<id>`: las tablas son por año y el `id` solo es único en su año. */
	key: string;
	id: number;
	year: number;
	/** ISO en UTC con offset (`+00:00`). */
	ts: string;
	user_id: number | null;
	event_type: AuditEventType | string;
	method: string;
	path: string;
	status_code: number;
	duration_ms: number | null;
	ip: string | null;
	user_agent: string | null;
	/** `msg` de la respuesta (texto que vio la persona). */
	response_msg: string | null;
	/** Solo en pedir/verificar código: el correo con el que se intentó entrar. */
	login_email: string | null;
};

type AuditKind = 'read' | 'write';

type AuditEventsFilters = {
	page: number;
	page_size: number;
	user_id?: number;
	event_type?: AuditEventType;
	/** ISO con offset; incluida. */
	date_from?: string;
	/** ISO con offset; excluida. */
	date_to?: string;
	path?: string;
	kind?: AuditKind;
	only_errors?: boolean;
};

function listAuditEvents(filters: AuditEventsFilters) {
	return api.get<Paginated<AuditEvent>>('/audit-logs', filters);
}

export type { AuditEvent, AuditEventsFilters, AuditEventType, AuditKind };
export { listAuditEvents };
