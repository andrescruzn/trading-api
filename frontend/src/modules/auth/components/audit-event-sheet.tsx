import type { ReactNode } from 'react';
import { useState } from 'react';
import type { AuditEvent } from '@/modules/auth/api/audit.api';
import type { UserSummary } from '@/modules/auth/api/users.api';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import {
	auditEventTypeLabel,
	formatAuditTime,
	httpMethodLabel,
	isErrorStatus,
} from '@/modules/auth/lib/audit-labels';
import { Badge } from '@/modules/ui/components/badge';
import {
	Sheet,
	SheetContent,
	SheetDescription,
	SheetHeader,
	SheetTitle,
} from '@/modules/ui/components/sheet';

type AuditEventSheetProps = {
	/** `null` = cerrado. */
	event: AuditEvent | null;
	users: Map<number, UserSummary>;
	onClose: () => void;
};

function DetailRow({
	label,
	children,
}: {
	label: string;
	children: ReactNode;
}) {
	return (
		<div className="grid gap-1 border-b py-3 last:border-b-0 sm:grid-cols-[10rem_1fr] sm:gap-4">
			<dt className="text-sm text-muted-foreground">{label}</dt>
			<dd className="min-w-0 text-sm break-words">{children}</dd>
		</div>
	);
}

/** Detalle de un evento de auditoría: quién, qué, cuándo, desde dónde y qué respondió la app. */
export function AuditEventSheet({
	event,
	users,
	onClose,
}: AuditEventSheetProps) {
	// Se recuerda el último evento para que el contenido no se vacíe al cerrar.
	const [last, setLast] = useState<AuditEvent | null>(event);
	if (event && event.key !== last?.key) setLast(event);
	const current = event ?? last;

	return (
		<Sheet open={event !== null} onOpenChange={(open) => !open && onClose()}>
			<SheetContent className="data-[side=right]:w-full data-[side=right]:sm:max-w-xl">
				<SheetHeader className="pr-14">
					<SheetTitle>
						{current ? auditEventTypeLabel(current.event_type) : ''}
					</SheetTitle>
					<SheetDescription>
						{current
							? `${formatAuditTime(current.ts)} · hora de tu dispositivo`
							: ''}
					</SheetDescription>
				</SheetHeader>
				{current && (
					<dl className="flex flex-col overflow-y-auto px-4 pb-4">
						<DetailRow label="Persona">
							{current.user_id != null ? (
								<OwnerCell userId={current.user_id} users={users} />
							) : (
								<span className="text-muted-foreground">Sin sesión</span>
							)}
						</DetailRow>
						{current.login_email && (
							<DetailRow label="Correo usado para entrar">
								{current.login_email}
							</DetailRow>
						)}
						<DetailRow label="Acción">
							<span className="font-mono">
								{current.method} {current.path}
							</span>
							<span className="block text-xs text-muted-foreground">
								{httpMethodLabel(current.method)}
							</span>
						</DetailRow>
						<DetailRow label="Resultado">
							<Badge
								variant={
									isErrorStatus(current.status_code) ? 'destructive' : 'outline'
								}
							>
								{current.status_code}
							</Badge>
						</DetailRow>
						<DetailRow label="Mensaje que vio">
							{current.response_msg ?? (
								<span className="text-muted-foreground">—</span>
							)}
						</DetailRow>
						<DetailRow label="Duración">
							{current.duration_ms != null
								? `${current.duration_ms.toLocaleString('es-CO')} ms`
								: '—'}
						</DetailRow>
						<DetailRow label="IP">
							<span className="font-mono">{current.ip ?? '—'}</span>
						</DetailRow>
						<DetailRow label="Navegador">
							<span className="text-xs">{current.user_agent ?? '—'}</span>
						</DetailRow>
						<DetailRow label="Fecha en UTC">
							<span className="font-mono text-xs">{current.ts}</span>
						</DetailRow>
					</dl>
				)}
			</SheetContent>
		</Sheet>
	);
}
