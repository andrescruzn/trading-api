import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import type { PayoutKind } from '@/modules/fund/api/fund-payouts.api';
import { useCreatePayoutMethodMutation } from '@/modules/fund/hooks/use-fund-payouts-mutations';
import { PAYOUT_KIND_OPTIONS } from '@/modules/fund/lib/fund-payouts-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
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
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

const text = (message: string) =>
	z.string().trim().max(120, 'Máximo 120 caracteres').min(1, message);
const optional = z.string().trim().max(120, 'Máximo 120 caracteres');

const payoutSchema = z
	.object({
		kind: z.enum(['bank', 'nequi']),
		label: z
			.string()
			.trim()
			.min(1, 'Ponle un nombre')
			.max(80, 'Máximo 80 caracteres'),
		holder_name: text('Escribe el nombre del titular'),
		document_number: text('Escribe el documento del titular'),
		bank_name: optional,
		account_type: optional,
		account_number: optional,
		phone: optional,
	})
	.superRefine((value, ctx) => {
		const required =
			value.kind === 'bank'
				? (['bank_name', 'account_type', 'account_number'] as const)
				: (['phone'] as const);
		for (const key of required) {
			if (!value[key]) {
				ctx.addIssue({
					code: 'custom',
					path: [key],
					message: 'Completa este dato',
				});
			}
		}
	});

type PayoutValues = z.infer<typeof payoutSchema>;

const EMPTY: PayoutValues = {
	kind: 'bank',
	label: '',
	holder_name: '',
	document_number: '',
	bank_name: '',
	account_type: '',
	account_number: '',
	phone: '',
};

const FIELDS: Record<
	PayoutKind,
	{ name: keyof PayoutValues; label: string; placeholder: string }[]
> = {
	bank: [
		{ name: 'bank_name', label: 'Banco', placeholder: 'Bancolombia' },
		{ name: 'account_type', label: 'Tipo de cuenta', placeholder: 'Ahorros' },
		{
			name: 'account_number',
			label: 'Número de cuenta',
			placeholder: '000123456789',
		},
	],
	nequi: [
		{ name: 'phone', label: 'Celular de Nequi', placeholder: '3001234567' },
	],
};

type PayoutMethodDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
};

/** La persona registra a dónde le pagan sus retiros. Los datos van cifrados. */
export function PayoutMethodDialog({
	open,
	onOpenChange,
}: PayoutMethodDialogProps) {
	const mutation = useCreatePayoutMethodMutation();
	const form = useForm<PayoutValues>({
		resolver: zodResolver(payoutSchema),
		defaultValues: EMPTY,
	});
	const kind = useWatch({ control: form.control, name: 'kind' });

	useEffect(() => {
		if (open) form.reset(EMPTY);
	}, [open, form]);

	function handleSubmit(values: PayoutValues) {
		const keys = FIELDS[values.kind].map((field) => field.name);
		const input = {
			kind: values.kind,
			label: values.label,
			holder_name: values.holder_name,
			document_number: values.document_number,
			...Object.fromEntries(keys.map((key) => [key, values[key]])),
		};
		mutation.mutate(input, {
			onSuccess: () => {
				toast.add({
					title: 'Medio de pago guardado',
					description: 'Por seguridad podrás usarlo dentro de 48 horas.',
					type: 'success',
				});
				onOpenChange(false);
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos guardar el medio de pago',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Nuevo medio de pago</DialogTitle>
					<DialogDescription>
						A dónde te pagan los retiros. Los datos se guardan cifrados y solo
						los ve un super admin al pagarte. Un medio nuevo se puede usar 48
						horas después de registrarlo.
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
								name="kind"
								control={form.control}
								render={({ field }) => (
									<Field>
										<FieldLabel htmlFor="payout-kind" required>
											Tipo
										</FieldLabel>
										<OptionSelect
											id="payout-kind"
											value={field.value}
											onChange={(value) => field.onChange(value ?? 'bank')}
											options={PAYOUT_KIND_OPTIONS}
										/>
									</Field>
								)}
							/>
							{(
								[
									{
										name: 'label',
										label: 'Nombre para reconocerlo',
										placeholder: 'Mi cuenta de ahorros',
									},
									{
										name: 'holder_name',
										label: 'Titular',
										placeholder: 'Nombre completo',
									},
									{
										name: 'document_number',
										label: 'Documento del titular',
										placeholder: 'CC 1234567890',
									},
									...FIELDS[kind],
								] as {
									name: keyof PayoutValues;
									label: string;
									placeholder: string;
								}[]
							).map((item) => (
								<Controller
									key={item.name}
									name={item.name}
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor={`payout-${item.name}`} required>
												{item.label}
											</FieldLabel>
											<Input
												{...field}
												id={`payout-${item.name}`}
												placeholder={item.placeholder}
												autoComplete="off"
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							))}
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
						Guardar medio de pago
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
