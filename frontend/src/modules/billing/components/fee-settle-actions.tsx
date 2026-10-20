import { IconCheck, IconLoader2, IconX } from '@tabler/icons-react';
import { useState } from 'react';
import type {
	FeeSettleAction,
	FeeTransaction,
} from '@/modules/billing/api/billing.api';
import { useSettleFeeMutation } from '@/modules/billing/hooks/use-billing-mutations';
import { formatPrice } from '@/modules/shared/lib/format';
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
import { Field, FieldLabel } from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

const COPY: Record<
	FeeSettleAction,
	{ title: string; body: string; button: string; done: string }
> = {
	charge: {
		title: '¿Marcar la comisión como cobrada?',
		body: 'Queda registrada con la fecha de hoy. Úsalo cuando el pago ya llegó.',
		button: 'Marcar cobrada',
		done: 'Comisión marcada como cobrada',
	},
	waive: {
		title: '¿Condonar la comisión?',
		body: 'No se le cobrará al inversor. No se puede deshacer.',
		button: 'Condonar',
		done: 'Comisión condonada',
	},
};

/** Botones del admin para una comisión pendiente (con confirmación y nota). */
export function FeeSettleActions({ fee }: { fee: FeeTransaction }) {
	const settleMutation = useSettleFeeMutation();
	const [action, setAction] = useState<FeeSettleAction | null>(null);
	const [notes, setNotes] = useState('');

	if (fee.status !== 'pending') return null;

	function confirm() {
		if (!action) return;
		settleMutation.mutate(
			{ id: fee.id, action, notes: notes.trim() || null },
			{
				onSuccess: () => {
					toast.add({ title: COPY[action].done, type: 'success' });
					setAction(null);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos actualizar la comisión',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<>
			<div className="flex justify-end gap-1">
				<Button
					size="sm"
					variant="ghost"
					onClick={() => {
						setNotes('');
						setAction('charge');
					}}
				>
					<IconCheck />
					Cobrada
				</Button>
				<Button
					size="sm"
					variant="ghost"
					className="text-muted-foreground"
					onClick={() => {
						setNotes('');
						setAction('waive');
					}}
				>
					<IconX />
					Condonar
				</Button>
			</div>
			<AlertDialog
				open={!!action}
				onOpenChange={(open) => !open && setAction(null)}
			>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>
							{action ? COPY[action].title : ''}
						</AlertDialogTitle>
						<AlertDialogDescription>
							Comisión del período #{fee.billing_period_id} por{' '}
							{formatPrice(fee.amount)}. {action ? COPY[action].body : ''}
						</AlertDialogDescription>
					</AlertDialogHeader>
					<Field>
						<FieldLabel htmlFor={`fee-notes-${fee.id}`}>
							Nota (opcional)
						</FieldLabel>
						<Input
							id={`fee-notes-${fee.id}`}
							value={notes}
							maxLength={500}
							placeholder={
								action === 'waive' ? 'Motivo' : 'Referencia del pago'
							}
							onChange={(event) => setNotes(event.target.value)}
						/>
					</Field>
					<AlertDialogFooter>
						<AlertDialogCancel>Volver</AlertDialogCancel>
						<AlertDialogAction
							variant={action === 'waive' ? 'destructive' : 'default'}
							disabled={settleMutation.isPending}
							onClick={confirm}
						>
							{settleMutation.isPending && (
								<IconLoader2 className="animate-spin" />
							)}
							{action ? COPY[action].button : ''}
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</>
	);
}
