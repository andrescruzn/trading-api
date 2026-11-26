import { IconCheck, IconLoader2, IconX } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import type { BotMode, Signal } from '@/modules/bots/api/bots.api';
import {
	useApproveSignalMutation,
	useRejectSignalMutation,
} from '@/modules/bots/hooks/use-bots-mutations';
import { toTimestamp } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from '@/modules/ui/components/alert-dialog';
import { Button } from '@/modules/ui/components/button';
import { toast } from '@/modules/ui/components/toast';

type SignalDecisionActionsProps = {
	signal: Pick<Signal, 'id' | 'decision_status' | 'expires_at'>;
	/** Live pide confirmación extra: la orden usa dinero real. */
	botMode?: BotMode;
	size?: 'xs' | 'sm' | 'default';
	onDecided?: () => void;
};

/** Minutos que faltan para que venza, redondeando hacia arriba; `null` sin límite. */
function minutesLeft(expiresAt: string | null, now: number): number | null {
	const expiresMs = toTimestamp(expiresAt);
	if (expiresMs === null) return null;
	return Math.max(0, Math.ceil((expiresMs - now) / 60_000));
}

function formatTimeLeft(minutes: number): string {
	if (minutes <= 0) return 'Vencida';
	if (minutes < 60) return `Vence en ${minutes} min`;
	const hours = Math.floor(minutes / 60);
	const rest = minutes % 60;
	return rest ? `Vence en ${hours} h ${rest} min` : `Vence en ${hours} h`;
}

/** Re-render cada 30 s para la cuenta atrás (no hace falta precisión de segundos). */
function useNow(intervalMs = 30_000): number {
	const [now, setNow] = useState(() => Date.now());
	useEffect(() => {
		const id = window.setInterval(() => setNow(Date.now()), intervalMs);
		return () => window.clearInterval(id);
	}, [intervalMs]);
	return now;
}

/**
 * Aprobar o descartar una señal pendiente (modo Con aprobación). Al aprobar,
 * el servidor revalida el precio actual antes de enviar la orden.
 */
export function SignalDecisionActions({
	signal,
	botMode,
	size = 'sm',
	onDecided,
}: SignalDecisionActionsProps) {
	const canManage = useCanManage();
	const approve = useApproveSignalMutation();
	const reject = useRejectSignalMutation();
	const [confirmLive, setConfirmLive] = useState(false);
	const now = useNow();

	// Solo un super admin cambia cosas: el socio ve el agente en solo lectura.
	if (!canManage) return null;

	if (signal.decision_status !== 'pending') return null;

	const left = minutesLeft(signal.expires_at, now);
	const expired = left === 0;
	const busy = approve.isPending || reject.isPending;

	function runApprove() {
		approve.mutate(signal.id, {
			onSuccess: () => {
				toast.add({ title: 'Orden enviada', type: 'success' });
				setConfirmLive(false);
				onDecided?.();
			},
			onError: (error) =>
				toast.add({
					title: 'No se ejecutó la señal',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	function runReject() {
		reject.mutate(signal.id, {
			onSuccess: () => {
				toast.add({ title: 'Señal descartada', type: 'info' });
				onDecided?.();
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos descartar la señal',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<div className="flex flex-wrap items-center gap-2">
			<Button
				size={size}
				disabled={busy || expired}
				onClick={() =>
					botMode === 'live' ? setConfirmLive(true) : runApprove()
				}
			>
				{approve.isPending ? (
					<IconLoader2 className="animate-spin" />
				) : (
					<IconCheck />
				)}
				Aprobar
			</Button>
			<Button
				size={size}
				variant="outline"
				disabled={busy || expired}
				onClick={runReject}
			>
				{reject.isPending ? (
					<IconLoader2 className="animate-spin" />
				) : (
					<IconX />
				)}
				Descartar
			</Button>
			{left !== null && (
				<span className="text-xs text-muted-foreground tabular-nums">
					{formatTimeLeft(left)}
				</span>
			)}

			<AlertDialog open={confirmLive} onOpenChange={setConfirmLive}>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>
							¿Enviar la orden con dinero real?
						</AlertDialogTitle>
						<AlertDialogDescription>
							Es un agente real. La orden sale a Binance con el precio actual si
							todavía cumple el stop loss y el riesgo/beneficio mínimo de 2:1.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel>Cancelar</AlertDialogCancel>
						<AlertDialogAction disabled={busy} onClick={runApprove}>
							{approve.isPending && <IconLoader2 className="animate-spin" />}
							Enviar orden
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</div>
	);
}
