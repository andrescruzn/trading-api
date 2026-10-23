import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { useCreateWithdrawalMutation } from '@/modules/fund/hooks/use-fund-payouts-mutations';
import {
	useMyPayoutMethodsQuery,
	useMyWithdrawableQuery,
} from '@/modules/fund/hooks/use-fund-payouts-queries';
import { positiveAmountField } from '@/modules/fund/lib/fund-forms';
import { OptionSelect } from '@/modules/shared/components/option-select';
import {
	formatDateTime,
	formatNumber,
	toTimestamp,
} from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
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
import { toast } from '@/modules/ui/components/toast';

const withdrawalSchema = z.object({
	payout_method_id: requiredSelectField('Elige a dónde te pagamos'),
	amount: positiveAmountField,
});

type WithdrawalInput = z.input<typeof withdrawalSchema>;
type WithdrawalOutput = z.output<typeof withdrawalSchema>;

type WithdrawalDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
};

/** Pedir un retiro del saldo disponible a banco o Nequi. */
export function WithdrawalDialog({
	open,
	onOpenChange,
}: WithdrawalDialogProps) {
	const methodsQuery = useMyPayoutMethodsQuery();
	const withdrawableQuery = useMyWithdrawableQuery();
	const mutation = useCreateWithdrawalMutation();
	const form = useForm<WithdrawalInput, unknown, WithdrawalOutput>({
		resolver: zodResolver(withdrawalSchema),
		defaultValues: { payout_method_id: null, amount: '' },
	});

	useEffect(() => {
		if (open) form.reset({ payout_method_id: null, amount: '' });
	}, [open, form]);

	const now = Date.now();
	const options = (methodsQuery.data ?? [])
		.filter((method) => method.is_active)
		.map((method) => {
			const ready = (toTimestamp(method.usable_from) ?? 0) <= now;
			return {
				value: String(method.id),
				label: ready
					? `${method.label} · ${method.masked}`
					: `${method.label} · disponible el ${formatDateTime(method.usable_from)}`,
				disabled: !ready,
			};
		});
	const withdrawable = withdrawableQuery.data?.withdrawable ?? '0';

	function handleSubmit(values: WithdrawalOutput) {
		mutation.mutate(
			{
				amount: values.amount,
				payout_method_id: Number(values.payout_method_id),
			},
			{
				onSuccess: () => {
					toast.add({
						title: 'Retiro pedido',
						description: 'Un super admin te paga y lo verás como pagado aquí.',
						type: 'success',
					});
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos pedir el retiro',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Retirar dinero</DialogTitle>
					<DialogDescription>
						Puedes retirar hasta {formatNumber(withdrawable, 2)} USDT: lo que ya
						pasó por un agente. Te pagamos en pesos a tu cuenta, a la tasa del
						día del pago.
					</DialogDescription>
				</DialogHeader>
				<form
					id="withdrawal-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="payout_method_id"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="withdrawal-method" required>
											A dónde
										</FieldLabel>
										<OptionSelect
											id="withdrawal-method"
											value={field.value}
											onChange={field.onChange}
											options={options}
											placeholder={
												options.length === 0
													? 'Primero registra un medio de pago'
													: 'Elige un medio de pago'
											}
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="amount"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="withdrawal-amount" required>
											Monto (USDT)
										</FieldLabel>
										<Input
											{...field}
											id="withdrawal-amount"
											inputMode="decimal"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Si tu dinero está en un agente, primero pide la salida
											desde «Mis agentes».
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
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button
						type="submit"
						form="withdrawal-form"
						disabled={mutation.isPending}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Pedir retiro
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
