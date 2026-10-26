import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import { useCreateWithdrawalMutation } from '@/modules/fund/hooks/use-fund-payouts-mutations';
import {
	useMyPayoutMethodsQuery,
	useMyWithdrawableQuery,
	useWithdrawNetworksQuery,
} from '@/modules/fund/hooks/use-fund-payouts-queries';
import { positiveAmountField } from '@/modules/fund/lib/fund-forms';
import { payoutNetwork } from '@/modules/fund/lib/fund-payouts-labels';
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
	payout_method_id: requiredSelectField('Elige a dónde te lo enviamos'),
	amount: positiveAmountField,
});

type WithdrawalInput = z.input<typeof withdrawalSchema>;
type WithdrawalOutput = z.output<typeof withdrawalSchema>;

type WithdrawalDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
};

/** Pedir un retiro del saldo disponible a una dirección cripto propia. */
export function WithdrawalDialog({
	open,
	onOpenChange,
}: WithdrawalDialogProps) {
	const methodsQuery = useMyPayoutMethodsQuery();
	const withdrawableQuery = useMyWithdrawableQuery();
	const networksQuery = useWithdrawNetworksQuery(open);
	const mutation = useCreateWithdrawalMutation();
	const form = useForm<WithdrawalInput, unknown, WithdrawalOutput>({
		resolver: zodResolver(withdrawalSchema),
		defaultValues: { payout_method_id: null, amount: '' },
	});

	useEffect(() => {
		if (open) form.reset({ payout_method_id: null, amount: '' });
	}, [open, form]);

	const methodId = useWatch({
		control: form.control,
		name: 'payout_method_id',
	});
	const amount = useWatch({ control: form.control, name: 'amount' });

	const now = Date.now();
	const methods = (methodsQuery.data ?? []).filter(
		(method) => method.is_active && method.kind === 'crypto',
	);
	const options = methods.map((method) => {
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

	// Comisión de red de la dirección elegida: la persona recibe monto − comisión
	const network = networksQuery.data?.networks.find(
		(item) =>
			item.network ===
			payoutNetwork(methods.find((method) => String(method.id) === methodId)),
	);
	const fee = network?.fee != null ? Number(network.fee) : null;
	const receives =
		fee !== null && Number(amount) > fee ? Number(amount) - fee : null;

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
						description:
							'Te avisaremos cuando enviemos el dinero a tu dirección.',
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
						pasó por un agente. Te lo enviamos desde la billetera de Binance a
						tu dirección; la comisión de red se descuenta de lo que recibes.
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
													? 'Primero registra una dirección de retiro'
													: 'Elige una dirección'
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
											{fee !== null
												? `Comisión de red: ${formatNumber(fee, 2)} USDT${receives !== null ? `. Recibirás cerca de ${formatNumber(receives, 2)} USDT.` : '.'}`
												: 'Si tu dinero está en un agente, primero pide la salida desde «Mis agentes».'}
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
