import type {
	BotExecutionMode,
	BotHistoryEntry,
	BotMode,
	BotStatus,
} from '@/modules/bots/api/bots.api';
import {
	BOT_MODE_LABELS,
	BOT_STATUS_LABELS,
	EXECUTION_MODE_LABELS,
} from '@/modules/bots/lib/bots-labels';
import { formatPercent } from '@/modules/shared/lib/format';

/** Motivos con los que el sistema cambia el estado de un agente por su cuenta. */
const SYSTEM_REASON_LABELS: Record<string, string> = {
	BOT_MAX_DRAWDOWN_REACHED:
		'Se detuvo por error: alcanzó su pérdida máxima permitida',
	OWNER_DISABLED: 'Se pausó porque se desactivó la cuenta de su dueño',
};

function statusLabel(value: unknown): string {
	return BOT_STATUS_LABELS[value as BotStatus] ?? String(value ?? '—');
}

function executionModeLabel(value: unknown): string {
	return EXECUTION_MODE_LABELS[value as BotExecutionMode] ?? String(value);
}

function riskPctLabel(value: unknown): string {
	return formatPercent(value as number | string | null, 1);
}

function riskPctOf(params: unknown): unknown {
	return params && typeof params === 'object'
		? (params as Record<string, unknown>).risk_pct
		: undefined;
}

function approvalTtlLabel(value: unknown): string {
	return value == null ? 'el valor por defecto' : `${value} min`;
}

/** "Inició el agente", "Pausó el agente"… según el estado al que pasó. */
function describeStatusChange(data: Record<string, unknown>): string {
	if (typeof data.reason === 'string') {
		return (
			SYSTEM_REASON_LABELS[data.reason] ?? `Pasó a ${statusLabel(data.to)}`
		);
	}
	switch (data.to) {
		case 'running':
			return data.from === 'paused' ? 'Reanudó el agente' : 'Inició el agente';
		case 'paused':
			return 'Pausó el agente';
		case 'stopped':
			return 'Detuvo el agente';
		default:
			return `Pasó a ${statusLabel(data.to)}`;
	}
}

/** Una frase por campo cambiado. */
function describeChange(
	field: string,
	before: unknown,
	after: unknown,
): string {
	switch (field) {
		case 'name':
			return `Cambió el nombre de «${before}» a «${after}»`;
		case 'risk_params': {
			const [from, to] = [riskPctOf(before), riskPctOf(after)];
			return from !== to
				? `Cambió el riesgo por operación de ${riskPctLabel(from)} a ${riskPctLabel(to)}`
				: 'Cambió los límites de riesgo';
		}
		case 'execution_mode':
			return `Cambió el modo de ejecución de ${executionModeLabel(before)} a ${executionModeLabel(after)}`;
		case 'approval_ttl_minutes':
			return `Cambió el tiempo para aprobar de ${approvalTtlLabel(before)} a ${approvalTtlLabel(after)}`;
		case 'share_signals':
			return after
				? 'Empezó a compartir sus señales'
				: 'Dejó de compartir sus señales';
		default:
			return `Cambió ${field}`;
	}
}

/** Texto de un evento del historial, listo para mostrar. */
function describeHistoryEntry(entry: BotHistoryEntry): string {
	const { data } = entry;
	switch (entry.event_type) {
		case 'BOT_CREATED':
			return `Creó el agente (${BOT_MODE_LABELS[data.mode as BotMode] ?? data.mode} · ${executionModeLabel(data.execution_mode)} · riesgo ${riskPctLabel(data.risk_pct)})`;
		case 'BOT_UPDATED': {
			const changes = (data.changes ?? {}) as Record<string, unknown[]>;
			const lines = Object.entries(changes).map(([field, [before, after]]) =>
				describeChange(field, before, after),
			);
			return lines.length > 0 ? lines.join(' · ') : 'Editó el agente';
		}
		case 'BOT_STATUS_CHANGED':
			return describeStatusChange(data);
		default:
			return entry.event_type;
	}
}

export { describeHistoryEntry };
