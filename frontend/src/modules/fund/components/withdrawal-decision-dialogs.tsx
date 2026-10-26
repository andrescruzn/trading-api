import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import type {
	Withdrawal,
	WithdrawalCheck,
} from '@/modules/fund/api/fund-payouts.api';
import { CopyText } from '@/modules/fund/components/copy-text';
import { ReceiptField } from '@/modules/fund/components/receipt-controls';
import {
	useCancelWithdrawalMutation,
	useLookupWithdrawalMutation,
	usePayWithdrawalMutation,
	useRejectWithdrawalMutation,
} from '@/modules/fund/hooks/use-fund-payouts-mutations';
import { usePayoutDetailsQuery } from '@/modules/fund/hooks/use-fund-payouts-queries';
import { fileToReceipt, receiptFileError } from '@/modules/fund/lib/fund-files';
import { requiredText } from '@/modules/fund/lib/fund-forms';
import {
	EXCHANGE_TX_STATUS_LABELS,
	PAYOUT_DETAIL_LABELS,
} from '@/modules/fund/lib/fund-payouts-labels';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { formatNumber } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
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
// Registrar el envío (super admin)
// ======================================================================

const optionalAmount = z
	.string()
	.trim()
	.transform((value) => value.replace(',', '.'))
	.refine(
		(value) =>
			value === '' || (Number.isFinite(Number(value)) && Number(value) >= 0),
		'Debe ser un número mayor o igual que 0',
	);

const paySchema = z.object({
	txid: requiredText('Pega el ID de la transacción', 160),
	sent_amount: optionalAmount,
	network_fee: optionalAmount,
	note: z.string().trim().max(500, 'Máximo 500 caracteres'),
});

type PayInput = z.input<typeof paySchema>;
type PayOutput = z.output<typeof paySchema>;

const EMPTY_PAY: PayInput = {
	txid: '',
	sent_amount: '',
	network_fee: '',
	note: '',
};

/** Resultado de buscar el txid en Binance, en palabras. */
function CheckResult({ check }: { check: WithdrawalCheck }) {
	if (!check.is_live) {
		return (
			<Alert>
				<AlertTitle>Billetera de práctica</AlertTitle>
				<AlertDescription>
					No hay exchange para comprobarlo: escribe lo que recibió la persona y
					la comisión de red.
				</AlertDescription>
			</Alert>
		);
	}
	if (!check.found) {
		return (
			<Alert variant="destructive">
				<AlertTitle>
					{check.exchange_error
						? 'Binance no respondió'
						: 'No encontramos ese envío en Binance'}
				</AlertTitle>
				<AlertDescription>
					Revisa el ID. Si estás seguro de que salió, escribe lo que recibió la
					persona, la comisión de red y una nota que lo explique.
				</AlertDescription>
			</Alert>
		);
	}
	const blocked = check.status !== 'ok' || check.address_matches === false;
	return (
		<Alert variant={blocked ? 'destructive' : 'default'}>
			<AlertTitle>
				Envío {EXCHANGE_TX_STATUS_LABELS[check.status ?? ''] ?? check.status} en
				Binance
			</AlertTitle>
			<AlertDescription>
				<span>
					Recibe {formatNumber(check.sent_amount, 2)} USDT · comisión{' '}
					{formatNumber(check.network_fee, 2)} USDT · red {check.network ?? '—'}
				</span>
				{check.address_matches === false && (
					<span>
						No fue a la dirección de la persona: no se puede registrar.
					</span>
				)}
				{check.address_matches === null && (
					<span>
						Binance no muestra la dirección de destino: agrega una nota.
					</span>
				)}
				{check.amount_matches === false && (
					<span>
						Enviado + comisión no coincide con lo pedido: agrega una nota.
					</span>
				)}
				{check.status === 'pending' && (
					<span>Regístralo cuando Binance lo muestre como completado.</span>
				)}
			</AlertDescription>
		</Alert>
	);
}

/**
 * El super admin envía el retiro desde Binance a la dirección de la persona
 * (sin bancos) y aquí registra el ID de la transacción. Con billetera live la
 * app lo busca en Binance y trae lo enviado y la comisión de red. La
 * dirección completa solo se muestra mientras el diálogo está abierto.
 */
export function PayWithdrawalDialog({
	withdrawal,
	onClose,
}: DecisionDialogProps) {
	const detailsQuery = usePayoutDetailsQuery(withdrawal?.id ?? null);
	const lookupMutation = useLookupWithdrawalMutation();
	const mutation = usePayWithdrawalMutation();
	const form = useForm<PayInput, unknown, PayOutput>({
		resolver: zodResolver(paySchema),
		defaultValues: EMPTY_PAY,
	});
	const txid = useWatch({ control: form.control, name: 'txid' });
	const [check, setCheck] = useState<WithdrawalCheck | null>(null);
	const [receiptFile, setReceiptFile] = useState<File | null>(null);

	useEffect(() => {
		if (!withdrawal) return;
		form.reset(EMPTY_PAY);
		setCheck(null);
		setReceiptFile(null);
	}, [withdrawal, form]);

	// Otro txid invalida la búsqueda anterior
	useEffect(() => {
		setCheck((current) =>
			current && current.txid !== txid.trim() ? null : current,
		);
	}, [txid]);

	const method = detailsQuery.data;
	const manual = check !== null && !check.found;

	function lookup() {
		if (!withdrawal || !txid.trim()) {
			form.setError('txid', { message: 'Pega el ID de la transacción' });
			return;
		}
		lookupMutation.mutate(
			{ id: withdrawal.id, txid: txid.trim() },
			{
				onSuccess: (result) => setCheck({ ...result, txid: txid.trim() }),
				onError: (error) =>
					toast.add({
						title: 'No pudimos buscar el envío',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	async function handleSubmit(values: PayOutput) {
		if (!withdrawal || !check || receiptFileError(receiptFile)) return;
		if (manual && !values.sent_amount) {
			form.setError('sent_amount', {
				message: 'Escribe lo que recibió la persona',
			});
			return;
		}
		const receipt = receiptFile ? await fileToReceipt(receiptFile) : null;
		mutation.mutate(
			{
				id: withdrawal.id,
				txid: values.txid,
				sent_amount: manual ? values.sent_amount : null,
				network_fee: manual ? values.network_fee || '0' : null,
				note: values.note || null,
				receipt,
			},
			{
				onSuccess: () => {
					toast.add({
						title: 'Envío registrado',
						description: 'Le avisamos a la persona con los detalles.',
						type: 'success',
					});
					onClose();
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos registrar el envío',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	const blocked =
		check?.found === true &&
		(check.status !== 'ok' || check.address_matches === false);

	return (
		<Dialog open={!!withdrawal} onOpenChange={(open) => !open && onClose()}>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle>
						Enviar {withdrawal ? formatNumber(withdrawal.amount, 2) : ''} USDT
					</DialogTitle>
					<DialogDescription>
						Haz el retiro en Binance por este monto, a esta dirección y por esta
						red. Binance descuenta la comisión de red de lo que recibe la
						persona. Luego pega aquí el ID de la transacción.
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
										title="No pudimos leer la dirección"
										error={detailsQuery.error}
									/>
								) : (
									<>
										<span className="text-sm font-medium">{method.label}</span>
										{Object.entries(method.details ?? {})
											.filter(([, value]) => !!value)
											.map(([key, value]) => (
												<div
													key={key}
													className="flex items-center justify-between gap-4 text-sm"
												>
													<span className="text-muted-foreground">
														{PAYOUT_DETAIL_LABELS[key] ?? key}
													</span>
													<CopyText value={value} label="Dato" />
												</div>
											))}
										{withdrawal && (
											<div className="flex items-center justify-between gap-4 text-sm">
												<span className="text-muted-foreground">Monto</span>
												<CopyText value={withdrawal.amount} label="Monto" />
											</div>
										)}
									</>
								)}
							</div>
							<Controller
								name="txid"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="pay-txid" required>
											ID de la transacción (TxID)
										</FieldLabel>
										<div className="flex gap-2">
											<Input
												{...field}
												id="pay-txid"
												autoComplete="off"
												spellCheck={false}
												className="font-mono"
												aria-invalid={fieldState.invalid}
											/>
											<Button
												type="button"
												variant="outline"
												onClick={lookup}
												disabled={lookupMutation.isPending}
											>
												{lookupMutation.isPending && (
													<IconLoader2 className="animate-spin" />
												)}
												Buscar en Binance
											</Button>
										</div>
										<FieldDescription>
											Cópialo del historial de retiros de Binance.
										</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							{check && <CheckResult check={check} />}
							{manual && (
								<div className="grid gap-4 sm:grid-cols-2">
									<Controller
										name="sent_amount"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="pay-sent" required>
													Recibió (USDT)
												</FieldLabel>
												<Input
													{...field}
													id="pay-sent"
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
										name="network_fee"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="pay-fee">
													Comisión de red (USDT)
												</FieldLabel>
												<Input
													{...field}
													id="pay-fee"
													inputMode="decimal"
													placeholder="0"
													aria-invalid={fieldState.invalid}
												/>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
								</div>
							)}
							<Controller
								name="note"
								control={form.control}
								render={({ field }) => (
									<Field>
										<FieldLabel htmlFor="pay-note">Nota</FieldLabel>
										<Textarea
											{...field}
											id="pay-note"
											rows={2}
											maxLength={500}
										/>
										<FieldDescription>
											Obligatoria si Binance no muestra el envío o el monto no
											coincide. La persona la ve en su historial.
										</FieldDescription>
									</Field>
								)}
							/>
							<ReceiptField
								id="pay-receipt"
								file={receiptFile}
								onChange={setReceiptFile}
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
						disabled={
							!check ||
							blocked ||
							mutation.isPending ||
							!!receiptFileError(receiptFile)
						}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Registrar envío
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
