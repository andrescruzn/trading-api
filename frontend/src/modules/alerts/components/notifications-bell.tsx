import { IconBell } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
import type { AlertSeverity } from '@/modules/alerts/api/alerts.api';
import type { AppNotification } from '@/modules/alerts/api/notifications.api';
import { useMarkNotificationsSeenMutation } from '@/modules/alerts/hooks/use-notifications-mutations';
import { useNotificationsQuery } from '@/modules/alerts/hooks/use-notifications-queries';
import { SEVERITY_LABELS } from '@/modules/alerts/lib/alerts-labels';
import { formatDateTime } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';
import {
	Popover,
	PopoverContent,
	PopoverDescription,
	PopoverHeader,
	PopoverTitle,
	PopoverTrigger,
} from '@/modules/ui/components/popover';
import { Separator } from '@/modules/ui/components/separator';
import { Skeleton } from '@/modules/ui/components/skeleton';
import { cn } from '@/modules/ui/lib/utils';

/** Punto de color por severidad (solo tokens de `index.css`). */
const SEVERITY_DOT: Record<AlertSeverity, string> = {
	info: 'bg-chart-2',
	warning: 'bg-chart-3',
	critical: 'bg-destructive',
};

/** El contador del badge se corta en 9+ para no ensanchar el botón. */
function formatUnread(count: number) {
	return count > 9 ? '9+' : String(count);
}

function NotificationItem({
	notification,
	highlighted,
}: {
	notification: AppNotification;
	highlighted: boolean;
}) {
	return (
		<li
			className={cn(
				'flex gap-3 rounded-md px-2 py-2',
				highlighted && 'bg-accent text-accent-foreground',
			)}
		>
			<span
				aria-hidden
				className={cn(
					'mt-1.5 size-2 shrink-0 rounded-full',
					SEVERITY_DOT[notification.severity] ?? 'bg-muted-foreground',
				)}
			/>
			<div className="flex min-w-0 flex-1 flex-col gap-0.5">
				<p className="font-medium leading-snug">
					<span className="sr-only">
						{SEVERITY_LABELS[notification.severity] ?? notification.severity}
						{highlighted ? ', nueva: ' : ': '}
					</span>
					{notification.title}
				</p>
				{notification.message && (
					<p className="line-clamp-2 text-xs text-muted-foreground">
						{notification.message}
					</p>
				)}
				<time
					dateTime={notification.ts ?? undefined}
					className="text-xs text-muted-foreground"
				>
					{formatDateTime(notification.ts)}
				</time>
			</div>
		</li>
	);
}

function NotificationsEmpty({ onNavigate }: { onNavigate: () => void }) {
	return (
		<div className="flex flex-col items-center gap-3 px-2 py-6 text-center">
			<IconBell className="size-6 text-muted-foreground" aria-hidden />
			<p className="text-sm text-muted-foreground">
				Aún no tienes notificaciones. Aquí verás lo que avisen tus reglas de
				alerta: señales de tus agentes, errores o niveles de precio.
			</p>
			<Button
				size="sm"
				variant="outline"
				render={<Link to="/alerts" />}
				onClick={onNavigate}
			>
				Crear una regla
			</Button>
		</div>
	);
}

/**
 * Campana del header: últimas alertas del usuario con contador de no leídas.
 * Al abrirla se marcan como vistas en la cuenta (vale en todos los
 * dispositivos); mientras sigue abierta, las que eran nuevas se resaltan.
 */
export function NotificationsBell() {
	const [open, setOpen] = useState(false);
	// IDs nuevos al abrir: tras marcar como visto el refetch trae `is_new: false`
	// y sin esto el resaltado desaparecería antes de que la persona lo lea.
	const [highlightIds, setHighlightIds] = useState<ReadonlySet<number>>(
		() => new Set(),
	);
	const notificationsQuery = useNotificationsQuery();
	const markSeen = useMarkNotificationsSeenMutation();

	const items = notificationsQuery.data?.items ?? [];
	const unread = notificationsQuery.data?.unread_count ?? 0;

	function handleOpenChange(nextOpen: boolean) {
		setOpen(nextOpen);
		if (!nextOpen) {
			setHighlightIds(new Set());
			return;
		}
		setHighlightIds(
			new Set(items.filter((item) => item.is_new).map((item) => item.id)),
		);
		// Sin pendientes no hace falta escribir; si falla, el contador sigue
		// visible y se reintenta la próxima vez que se abra.
		if (unread > 0 && !markSeen.isPending) {
			markSeen.mutate();
		}
	}

	const close = () => handleOpenChange(false);
	// Vacío de verdad: hay respuesta y no trae eventos (no durante la carga ni con error).
	const isEmpty = !!notificationsQuery.data && items.length === 0;

	return (
		<Popover open={open} onOpenChange={handleOpenChange}>
			<PopoverTrigger
				render={
					<Button
						variant="ghost"
						size="icon-sm"
						className="relative"
						aria-label={
							unread > 0
								? `Notificaciones: ${unread} sin leer`
								: 'Notificaciones'
						}
					/>
				}
			>
				<IconBell />
				{unread > 0 && (
					<Badge
						aria-hidden
						className="absolute top-0.5 right-0.5 h-4 min-w-4 px-1 text-[0.625rem] tabular-nums"
					>
						{formatUnread(unread)}
					</Badge>
				)}
			</PopoverTrigger>
			<PopoverContent align="end" className="w-80 gap-2 p-2 sm:w-96">
				<PopoverHeader className="px-2 pt-2">
					<PopoverTitle>Notificaciones</PopoverTitle>
					<PopoverDescription>
						Lo último que avisaron tus alertas.
					</PopoverDescription>
				</PopoverHeader>
				<Separator />
				{notificationsQuery.isLoading ? (
					<div className="flex flex-col gap-2 p-2">
						<Skeleton className="h-12" />
						<Skeleton className="h-12" />
						<Skeleton className="h-12" />
					</div>
				) : notificationsQuery.isError && !notificationsQuery.data ? (
					<p className="px-2 py-6 text-center text-sm text-destructive">
						{getErrorMessage(notificationsQuery.error)}
					</p>
				) : isEmpty ? (
					<NotificationsEmpty onNavigate={close} />
				) : (
					<ul className="flex max-h-96 flex-col gap-1 overflow-y-auto">
						{items.map((item) => (
							<NotificationItem
								key={item.id}
								notification={item}
								highlighted={item.is_new || highlightIds.has(item.id)}
							/>
						))}
					</ul>
				)}
				{!isEmpty && (
					<>
						<Separator />
						<Button
							variant="ghost"
							size="sm"
							render={<Link to="/alerts" />}
							onClick={close}
						>
							Ver todas
						</Button>
					</>
				)}
			</PopoverContent>
		</Popover>
	);
}
