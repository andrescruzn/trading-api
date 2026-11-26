import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { DepositInfo } from '@/modules/fund/api/fund.api';
import { useCreateDepositMutation } from '@/modules/fund/hooks/use-fund-mutations';
import { positiveAmountField } from '@/modules/fund/lib/fund-forms';
import { OptionSelect } from '@/modules/shared/components/option-select';
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

const depositSchema = z.object({
	network: requiredSelectField('Elige la red por la que enviaste'),
	amount: positiveAmountField,
	txid: z
		.string()
		.trim()
		.min(10, 'Pega el ID completo de la transacción')
		.max(128, 'Máximo 128 caracteres'),
});

type DepositFormInput = z.input<typeof depositSchema>;
type DepositFormOutput = z.output<typeof depositSchema>;

type DepositFormDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	info: DepositInfo;
};

/** El participante registra un envío para que el sistema lo verifique. */
export function DepositFormDialog({
	open,
	onOpenChange,
	info,
}: DepositFormDialogProps) {
	const createMutation = useCreateDepositMutation();
	const asset = info.asset ?? 'USDT';
	const networkOptions = info.networks.map((network) => ({
		value: network.network,
		label: `${network.name} (${network.network})`,
	}));

	const form = useForm<DepositFormInput, unknown, DepositFormOutput>({
		resolver: zodResolver(depositSchema),
		defaultValues: { network: null, amount: '', txid: '' },
	});

	useEffect(() => {
		if (!open) return;
		form.reset({
			// Con una sola red, ya elegida
			network: info.networks.length === 1 ? info.networks[0].network : null,
			amount: '',
			txid: '',
		});
	}, [open, info.networks, form]);

	function handleSubmit(values: DepositFormOutput) {
		createMutation.mutate(
			{
				network: values.network as string,
				amount: values.amount,
				txid: values.txid,
			},
			{
				onSuccess: () => {
					toast.add({
						title: 'Depósito registrado',
						description: `Lo confirmamos en cuanto aparezca en el exchange (puede tardar unos minutos). Si en ${info.request_ttl_hours} horas no aparece, vence.`,
						type: 'success',
					});
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos registrar el depósito',
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
					<DialogTitle>Registrar depósito</DialogTitle>
					<DialogDescription>
						Hazlo después de enviar el dinero: con el ID de la transacción lo
						buscamos en la billetera de la plataforma y te lo acreditamos.
					</DialogDescription>
				</DialogHeader>
				<form
					id="deposit-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="network"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="deposit-network" required>
											Red
										</FieldLabel>
										<OptionSelect
											id="deposit-network"
											value={field.value}
											onChange={field.onChange}
											options={networkOptions}
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
										<FieldLabel htmlFor="deposit-amount" required>
											Monto enviado ({asset})
										</FieldLabel>
										<Input
											{...field}
											id="deposit-amount"
											inputMode="decimal"
											placeholder="1000"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Se acredita lo que reporte el exchange. Si no coincide con
											lo que escribes aquí, lo revisa un super admin.
										</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="txid"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="deposit-txid" required>
											ID de la transacción (TxID)
										</FieldLabel>
										<Input
											{...field}
											id="deposit-txid"
											className="font-mono"
											placeholder="Pégalo desde tu billetera"
											autoComplete="off"
											aria-invalid={fieldState.invalid}
										/>
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
						form="deposit-form"
						disabled={createMutation.isPending}
					>
						{createMutation.isPending && (
							<IconLoader2 className="animate-spin" />
						)}
						Registrar depósito
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
