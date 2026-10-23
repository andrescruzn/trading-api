import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import type { Withdrawal } from '@/modules/fund/api/fund-payouts.api';
import { CopyText } from '@/modules/fund/components/copy-text';
import {
	useCancelWithdrawalMutation,
	usePayWithdrawalMutation,
	useRejectWithdrawalMutation,
} from '@/modules/fund/hooks/use-fund-payouts-mutations';
import { usePayoutDetailsQuery } from '@/modules/fund/hooks/use-fund-payouts-queries';
import {
	positiveAmountField,
	requiredText,
} from '@/modules/fund/lib/fund-forms';
import {
	PAYOUT_DETAIL_LABELS,
	PAYOUT_KIND_LABELS,
} from '@/modules/fund/lib/fund-payouts-labels';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
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
import { Skeleton } from '@/modules/ui/components/skeleton';
import { Textarea } from '@/modules/ui/components/textarea';
import { toast } from '@/modules/ui/components/toast';

type DecisionDialogProps = {
	/** `null` = cerrado. */
	withdrawal: Withdrawal | null;
	onClose: () => void;
};

// ======================================================================
// Pagar (super admin)
// ======================================================================

const paySchema = z.object({
	cop_rate: positiveAmountField,
	paid_cop_amount: positiveAmountField,
	payment_reference: requiredText('Escribe la referencia del pago', 120),
	note: z.string().trim().max(500, 'Máximo 500 caracteres'),
});

type PayInput = z.input<typeof paySchema>;
type PayOutput = z.output<typeof paySchema>;

const EMPTY_PAY: PayInput = {
	cop_rate: '',
	paid_cop_amount: '',
	payment_reference: '',
	note: '',
};

/**
 * El super admin transfiere por fuera (banco o Nequi) y aquí lo registra:
 * pesos pagados, tasa y referencia. Muestra los datos completos del medio de
 * pago solo mientras el diálogo está abierto.
 */
export function PayWithdrawalDialog({
	withdrawal,
	onClose,
}: DecisionDialogProps) {
	const detailsQuery = usePayoutDetailsQuery(withdrawal?.id ?? null);
	const mutation = usePayWithdrawalMutation();
	const form = useForm<PayInput, unknown, PayOutput>({
		resolver: zodResolver(paySchema),
		defaultValues: EMPTY_PAY,
	});
	const rate = useWatch({ control: form.control, name: 'cop_rate' });

	useEffect(() => {
		if (withdrawal) form.reset(EMPTY_PAY);
	}, [withdrawal, form]);

	const rateNumber = Number(rate.trim().replace(',', '.'));
	const suggested =
		withdrawal && rateNumber > 0
			? Math.round(Number(withdrawal.amount) * rateNumber)
			: null;
	const method = detailsQuery.data;

	function handleSubmit(values: PayOutput) {
		if (!withdrawal) return;
		mutation.mutate(
			{
				id: withdrawal.id,
				cop_rate: values.cop_rate,
				paid_cop_amount: values.paid_cop_amount,
				payment_reference: values.payment_reference,
				note: values.note || null,
			},
			{
				onSuccess: () => {
					toast.add({ title: 'Retiro pagado', type: 'success' });
					onClose();
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos registrar el pago',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={!!withdrawal} onOpenChange={(open) => !open && onClose()}>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle>
						Pagar {withdrawal ? formatNumber(withdrawal.amount, 2) : ''} USDT
					</DialogTitle>
					<DialogDescription>
						Haz la transferencia desde el banco o Nequi y luego registra aquí lo
						que pagaste. Al guardar se descuenta del saldo disponible de la
						persona.
					</DialogDescription>
				</DialogHeader>
				<form
					id="pay-withdrawal-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<div className="flex flex-col gap-1.5 rounded-lg border p-3">
								{detailsQuery.isLoading ? (
									<>
										<Skeleton className="h-5 w-full" />
										<Skeleton className="h-5 w-2/3" />
									</>
								) : detailsQuery.error || !method ? (
									<ErrorAlert
										title="No pudimos leer el medio de pago"
										error={detailsQuery.error}
									/>
								) : (
									<>
										<span className="text-sm font-medium">
											{PAYOUT_KIND_LABELS[method.kind]} · {method.label}
										</span>
										{Object.entries(method.details ?? {}).map(
											([key, value]) => (
												<div
													key={key}
													className="flex items-center justify-between gap-4 text-sm"
												>
													<span className="text-muted-foreground">
														{PAYOUT_DETAIL_LABELS[key] ?? key}
													</span>
													<CopyText value={value} label="Dato" />
												</div>
											),
										)}
									</>
								)}
							</div>
							<Controller
								name="cop_rate"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="pay-rate" required>
											Tasa (COP por USDT)
										</FieldLabel>
										<Input
											{...field}
											id="pay-rate"
											inputMode="decimal"
											placeholder="4000"
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="paid_cop_amount"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="pay-cop" required>
											Pesos pagados (COP)
										</FieldLabel>
										<Input
											{...field}
											id="pay-cop"
											inputMode="decimal"
											aria-invalid={fieldState.invalid}
										/>
										{suggested !== null && (
											<FieldDescription>
												Con esa tasa serían {formatNumber(suggested, 0)} COP.
											</FieldDescription>
										)}
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="payment_reference"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="pay-reference" required>
											Referencia de la transferencia
										</FieldLabel>
										<Input
											{...field}
											id="pay-reference"
											autoComplete="off"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											La ve la persona para buscar el pago en su cuenta.
										</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="note"
								control={form.control}
								render={({ field }) => (
									<Field>
										<FieldLabel htmlFor="pay-note">Nota (opcional)</FieldLabel>
										<Textarea
											{...field}
											id="pay-note"
											rows={2}
											maxLength={500}
										/>
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
						form="pay-withdrawal-form"
						disabled={mutation.isPending}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Registrar pago
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
	note: requiredText('Escribe el motivo', 500, 3),
});

type RejectValues = z.infer<typeof rejectSchema>;

export function RejectWithdrawalDialog({
	withdrawal,
	onClose,
}: DecisionDialogProps) {
	const mutation = useRejectWithdrawalMutation();
	const form = useForm<RejectValues>({
		resolver: zodResolver(rejectSchema),
		defaultValues: { note: '' },
	});

	useEffect(() => {
		if (withdrawal) form.reset({ note: '' });
	}, [withdrawal, form]);

	function handleSubmit(values: RejectValues) {
		if (!withdrawal) return;
		mutation.mutate(
			{ id: withdrawal.id, note: values.note },
			{
				onSuccess: () => {
					toast.add({ title: 'Retiro rechazado', type: 'success' });
					onClose();
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos rechazar el retiro',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={!!withdrawal} onOpenChange={(open) => !open && onClose()}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Rechazar retiro</DialogTitle>
					<DialogDescription>
						El dinero vuelve a quedar disponible para la persona. Ella verá el
						motivo.
					</DialogDescription>
				</DialogHeader>
				<form
					id="reject-withdrawal-form"
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
									<FieldLabel htmlFor="reject-withdrawal-note" required>
										Motivo
									</FieldLabel>
									<Textarea
										{...field}
										id="reject-withdrawal-note"
										rows={3}
										maxLength={500}
										placeholder="Ej.: Los datos de la cuenta no coinciden con el titular."
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
						form="reject-withdrawal-form"
						variant="destructive"
						disabled={mutation.isPending}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Rechazar retiro
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}

// ======================================================================
// Anular (participante)
// ======================================================================

export function CancelWithdrawalDialog({
	withdrawal,
	onClose,
}: DecisionDialogProps) {
	const mutation = useCancelWithdrawalMutation();

	function cancel() {
		if (!withdrawal) return;
		mutation.mutate(withdrawal.id, {
			onSuccess: () => {
				toast.add({ title: 'Retiro anulado', type: 'success' });
				onClose();
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos anular el retiro',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<AlertDialog
			open={!!withdrawal}
			onOpenChange={(open) => !open && onClose()}
		>
			<AlertDialogContent>
				<AlertDialogHeader>
					<AlertDialogTitle>¿Anular este retiro?</AlertDialogTitle>
					<AlertDialogDescription>
						Los {withdrawal ? formatNumber(withdrawal.amount, 2) : ''} USDT
						vuelven a tu saldo disponible y no se te pagarán.
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
						Anular retiro
					</AlertDialogAction>
				</AlertDialogFooter>
			</AlertDialogContent>
		</AlertDialog>
	);
}
