import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { useCreatePayoutMethodMutation } from '@/modules/fund/hooks/use-fund-payouts-mutations';
import { useWithdrawNetworksQuery } from '@/modules/fund/hooks/use-fund-payouts-queries';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { formatNumber } from '@/modules/shared/lib/format';
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

const payoutSchema = z.object({
	label: z
		.string()
		.trim()
		.min(1, 'Ponle un nombre')
		.max(80, 'Máximo 80 caracteres'),
	network: requiredSelectField('Elige la red'),
	address: z
		.string()
		.trim()
		.min(1, 'Pega la dirección')
		.max(120, 'Máximo 120 caracteres')
		.refine((value) => !/\s/.test(value), 'La dirección no lleva espacios'),
	memo: z.string().trim().max(120, 'Máximo 120 caracteres'),
});

type PayoutInput = z.input<typeof payoutSchema>;
type PayoutOutput = z.output<typeof payoutSchema>;

const EMPTY: PayoutInput = { label: '', network: null, address: '', memo: '' };

type PayoutMethodDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
};

/**
 * La persona registra la dirección cripto a la que le enviamos sus retiros
 * (sin bancos: solo movimientos entre billeteras). Los datos van cifrados.
 */
export function PayoutMethodDialog({
	open,
	onOpenChange,
}: PayoutMethodDialogProps) {
	const networksQuery = useWithdrawNetworksQuery(open);
	const mutation = useCreatePayoutMethodMutation();
	const form = useForm<PayoutInput, unknown, PayoutOutput>({
		resolver: zodResolver(payoutSchema),
		defaultValues: EMPTY,
	});

	useEffect(() => {
		if (open) form.reset(EMPTY);
	}, [open, form]);

	const asset = networksQuery.data?.asset ?? 'USDT';
	const networks = networksQuery.data?.networks ?? [];
	const options = networks.map((item) => ({
		value: item.network,
		label:
			item.fee !== null
				? `${item.name} (${item.network}) · comisión ${formatNumber(item.fee, 2)} ${asset}`
				: `${item.name} (${item.network})`,
	}));

	function handleSubmit(values: PayoutOutput) {
		mutation.mutate(
			{
				label: values.label,
				network: values.network as string,
				address: values.address,
				memo: values.memo || undefined,
			},
			{
				onSuccess: () => {
					toast.add({
						title: 'Dirección guardada',
						description: 'Por seguridad podrás usarla dentro de 48 horas.',
						type: 'success',
					});
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos guardar la dirección',
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
					<DialogTitle>Nueva dirección de retiro</DialogTitle>
					<DialogDescription>
						La dirección de tu billetera a la que te enviamos los retiros en{' '}
						{asset}. Se guarda cifrada y solo la ve un super admin al enviarte
						el dinero. Una dirección nueva se puede usar 48 horas después de
						registrarla.
					</DialogDescription>
				</DialogHeader>
				<form
					id="payout-method-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="label"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="payout-label" required>
											Nombre para reconocerla
										</FieldLabel>
										<Input
											{...field}
											id="payout-label"
											placeholder="Mi billetera de Binance"
											autoComplete="off"
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="network"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="payout-network" required>
											Red
										</FieldLabel>
										<OptionSelect
											id="payout-network"
											value={field.value}
											onChange={field.onChange}
											options={options}
											placeholder={
												networksQuery.isLoading
													? 'Cargando redes…'
													: options.length === 0
														? 'El fondo aún no tiene redes configuradas'
														: 'Elige la red'
											}
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Usa la misma red en tu billetera: si la dirección es de
											otra red, el dinero se pierde.
										</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="address"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="payout-address" required>
											Dirección
										</FieldLabel>
										<Input
											{...field}
											id="payout-address"
											placeholder="Pégala desde tu billetera"
											autoComplete="off"
											spellCheck={false}
											className="font-mono"
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="memo"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="payout-memo">Memo</FieldLabel>
										<Input
											{...field}
											id="payout-memo"
											autoComplete="off"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Solo si tu billetera te lo pide para esta red (también se
											llama tag).
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
						form="payout-method-form"
						disabled={mutation.isPending}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Guardar dirección
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
