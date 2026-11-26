import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { DepositRequest } from '@/modules/fund/api/fund.api';
import {
	useCancelDepositMutation,
	useConfirmDepositMutation,
	useRejectDepositMutation,
} from '@/modules/fund/hooks/use-fund-mutations';
import { requiredText } from '@/modules/fund/lib/fund-forms';
import { formatNumber } from '@/modules/shared/lib/format';
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
import {
	Dialog,
	DialogBody,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from '@/modules/ui/components/dialog';
import {
	Field,
	FieldDescription,
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { Textarea } from '@/modules/ui/components/textarea';
import { toast } from '@/modules/ui/components/toast';

type DecisionDialogProps = {
	/** `null` = cerrado. */
	request: DepositRequest | null;
	onClose: () => void;
};

// ======================================================================
// Confirmar (super admin)
// ======================================================================

const confirmSchema = z.object({
	amount: z
		.string()
		.trim()
		.min(1, 'Escribe el monto')
		.transform((value) => value.replace(',', '.'))
		.refine(
			(value) => Number.isFinite(Number(value)) && Number(value) > 0,
			'Debe ser un número mayor que 0',
		),
	note: z.string().trim().max(500, 'Máximo 500 caracteres'),
});

type ConfirmInput = z.input<typeof confirmSchema>;
type ConfirmOutput = z.output<typeof confirmSchema>;

/**
 * Confirma un depósito y lo acredita al saldo pendiente de asignar. Si el
 * monto no es el que reportó el exchange (o el exchange no lo reportó), la
 * nota es obligatoria: el backend la exige y queda en el historial.
 */
export function ConfirmDepositDialog({
	request,
	onClose,
}: DecisionDialogProps) {
	const mutation = useConfirmDepositMutation();
	const form = useForm<ConfirmInput, unknown, ConfirmOutput>({
		resolver: zodResolver(confirmSchema),
		defaultValues: { amount: '', note: '' },
	});

	useEffect(() => {
		if (!request) return;
		form.reset({
			amount: request.credited_amount ?? request.declared_amount,
			note: '',
		});
	}, [request, form]);

	const backed = request?.credited_amount != null;

	function handleSubmit(values: ConfirmOutput) {
		if (!request) return;
		mutation.mutate(
			{ id: request.id, amount: values.amount, note: values.note || null },
			{
				onSuccess: () => {
					toast.add({ title: 'Depósito confirmado', type: 'success' });
					onClose();
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos confirmar el depósito',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={!!request} onOpenChange={(open) => !open && onClose()}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Confirmar depósito</DialogTitle>
					<DialogDescription>
						{request
							? `Declarado: ${formatNumber(request.declared_amount)} ${request.asset}. ${
									backed
										? `Según el exchange: ${formatNumber(request.credited_amount)} ${request.asset}.`
										: 'El exchange aún no lo reporta: revísalo allí antes de confirmar.'
								}`
							: ''}
					</DialogDescription>
				</DialogHeader>
				<form
					id="confirm-deposit-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="amount"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="confirm-amount" required>
											Monto a acreditar ({request?.asset ?? 'USDT'})
										</FieldLabel>
										<Input
											{...field}
											id="confirm-amount"
											inputMode="decimal"
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="note"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="confirm-note" required={!backed}>
											Nota
										</FieldLabel>
										<Textarea
											{...field}
											id="confirm-note"
											rows={3}
											placeholder="Ej.: Verificado en el historial de depósitos de Binance."
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Obligatoria si el monto no es el que reportó el exchange.
											La persona la ve en su historial.
										</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={onClose}>
						Cancelar
					</Button>
					<Button
						type="submit"
						form="confirm-deposit-form"
						disabled={mutation.isPending}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Confirmar y acreditar
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}

// ======================================================================
// Rechazar (super admin)
// ======================================================================

const rejectSchema = z.object({
	note: requiredText('Escribe el motivo: la persona lo ve en su historial'),
});

type RejectValues = z.infer<typeof rejectSchema>;

export function RejectDepositDialog({ request, onClose }: DecisionDialogProps) {
	const mutation = useRejectDepositMutation();
	const form = useForm<RejectValues>({
		resolver: zodResolver(rejectSchema),
		defaultValues: { note: '' },
	});

	useEffect(() => {
		if (request) form.reset({ note: '' });
	}, [request, form]);

	function handleSubmit(values: RejectValues) {
		if (!request) return;
		mutation.mutate(
			{ id: request.id, note: values.note },
			{
				onSuccess: () => {
					toast.add({ title: 'Depósito rechazado', type: 'success' });
					onClose();
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos rechazar el depósito',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={!!request} onOpenChange={(open) => !open && onClose()}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Rechazar depósito</DialogTitle>
					<DialogDescription>
						No se acredita nada. Si el dinero sí llegó a la billetera,
						devuélvelo desde el exchange.
					</DialogDescription>
				</DialogHeader>
				<form
					id="reject-deposit-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<Controller
							name="note"
							control={form.control}
							render={({ field, fieldState }) => (
								<Field data-invalid={fieldState.invalid}>
									<FieldLabel htmlFor="reject-note" required>
										Motivo
									</FieldLabel>
									<Textarea
										{...field}
										id="reject-note"
										rows={3}
										placeholder="Ej.: El txid corresponde a un envío a otra dirección."
										aria-invalid={fieldState.invalid}
									/>
									{fieldState.invalid && (
										<FieldError errors={[fieldState.error]} />
									)}
								</Field>
							)}
						/>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={onClose}>
						Cancelar
					</Button>
					<Button
						type="submit"
						form="reject-deposit-form"
						variant="destructive"
						disabled={mutation.isPending}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Rechazar depósito
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}

// ======================================================================
// Anular (participante)
// ======================================================================

export function CancelDepositDialog({ request, onClose }: DecisionDialogProps) {
	const mutation = useCancelDepositMutation();

	function cancel() {
		if (!request) return;
		mutation.mutate(request.id, {
			onSuccess: () => {
				toast.add({ title: 'Depósito anulado', type: 'success' });
				onClose();
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos anular el depósito',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<AlertDialog open={!!request} onOpenChange={(open) => !open && onClose()}>
			<AlertDialogContent>
				<AlertDialogHeader>
					<AlertDialogTitle>¿Anular este depósito?</AlertDialogTitle>
					<AlertDialogDescription>
						Deja de buscarse en el exchange. Hazlo solo si te equivocaste al
						registrarlo: si el dinero llegó, no se acreditará.
					</AlertDialogDescription>
				</AlertDialogHeader>
				<AlertDialogFooter>
					<AlertDialogCancel>Volver</AlertDialogCancel>
					<AlertDialogAction
						variant="destructive"
						disabled={mutation.isPending}
						onClick={cancel}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Anular depósito
					</AlertDialogAction>
				</AlertDialogFooter>
			</AlertDialogContent>
		</AlertDialog>
	);
}
