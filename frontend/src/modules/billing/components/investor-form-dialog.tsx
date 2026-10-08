import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { Investor } from '@/modules/billing/api/billing.api';
import {
	useCreateInvestorMutation,
	useUpdateInvestorMutation,
} from '@/modules/billing/hooks/use-billing-mutations';
import {
	fractionToPercentText,
	percentToFraction,
} from '@/modules/billing/lib/billing-labels';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button } from '@/modules/ui/components/button';
import { Checkbox } from '@/modules/ui/components/checkbox';
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

// En el formulario la comisión va en % (20 = 20 %); la API la recibe como
// fracción (0.2000), igual que hacía la versión anterior.
const investorSchema = z.object({
	user_id: z
		.string()
		.trim()
		.min(1, 'Escribe el ID del usuario')
		.pipe(
			z.coerce
				.number({ message: 'Escribe un número' })
				.int('Debe ser un número entero')
				.min(1, 'Debe ser mayor que 0'),
		),
	fee_percent: z
		.string()
		.trim()
		.min(1, 'Escribe la comisión')
		.pipe(
			z.coerce
				.number({ message: 'Escribe un número' })
				.min(0, 'Debe estar entre 0 y 100')
				.max(100, 'Debe estar entre 0 y 100'),
		),
	is_active: z.boolean(),
});

type InvestorFormInput = z.input<typeof investorSchema>;
type InvestorFormOutput = z.output<typeof investorSchema>;

type InvestorFormDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	/** `null` = crear; un inversor = editar (el usuario no se cambia). */
	investor: Investor | null;
};

export function InvestorFormDialog({
	open,
	onOpenChange,
	investor,
}: InvestorFormDialogProps) {
	const isEdit = !!investor;
	const createMutation = useCreateInvestorMutation();
	const updateMutation = useUpdateInvestorMutation();
	const isPending = createMutation.isPending || updateMutation.isPending;

	const form = useForm<InvestorFormInput, unknown, InvestorFormOutput>({
		resolver: zodResolver(investorSchema),
		defaultValues: { user_id: '', fee_percent: '', is_active: true },
	});

	useEffect(() => {
		if (!open) return;
		form.reset({
			user_id: investor ? String(investor.user_id) : '',
			fee_percent: investor ? fractionToPercentText(investor.fee_pct) : '',
			is_active: investor?.is_active ?? true,
		});
	}, [open, investor, form]);

	function handleSubmit(values: InvestorFormOutput) {
		const feePct = percentToFraction(values.fee_percent);
		const callbacks = {
			onSuccess: () => {
				toast.add({
					title: isEdit ? 'Inversor actualizado' : 'Inversor creado',
					type: 'success',
				});
				onOpenChange(false);
			},
			onError: (error: unknown) =>
				toast.add({
					title: isEdit
						? 'No pudimos actualizar el inversor'
						: 'No pudimos crear el inversor',
					description: getErrorMessage(error),
					type: 'error',
				}),
		};

		if (investor) {
			updateMutation.mutate(
				{ id: investor.id, input: { fee_pct: feePct, is_active: values.is_active } },
				callbacks,
			);
		} else {
			createMutation.mutate({ user_id: values.user_id, fee_pct: feePct }, callbacks);
		}
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>{isEdit ? 'Editar inversor' : 'Nuevo inversor'}</DialogTitle>
					<DialogDescription>
						{investor
							? `Inversor #${investor.id} · usuario #${investor.user_id}`
							: 'Perfil de inversor para un usuario con rol Inversor.'}
					</DialogDescription>
				</DialogHeader>
				<form
					id="investor-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							{!isEdit && (
								<Controller
									name="user_id"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="investor-user" required>
												ID del usuario
											</FieldLabel>
											<Input
												{...field}
												id="investor-user"
												type="number"
												inputMode="numeric"
												placeholder="12"
												aria-invalid={fieldState.invalid}
											/>
											<FieldDescription>
												El usuario debe tener el rol Inversor.
											</FieldDescription>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							)}
							<Controller
								name="fee_percent"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="investor-fee" required>
											Comisión de desempeño (%)
										</FieldLabel>
										<Input
											{...field}
											id="investor-fee"
											type="number"
											inputMode="decimal"
											step="0.01"
											min={0}
											max={100}
											placeholder="20"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Entre 0 y 100. Se cobra sobre la ganancia por encima de la marca de agua
											(HWM). Los períodos ya abiertos conservan la comisión anterior.
										</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							{isEdit && (
								<Controller
									name="is_active"
									control={form.control}
									render={({ field }) => (
										<Field orientation="horizontal">
											<Checkbox
												id="investor-active"
												checked={field.value}
												onCheckedChange={(checked) => field.onChange(checked)}
											/>
											<FieldLabel htmlFor="investor-active">Activo</FieldLabel>
										</Field>
									)}
								/>
							)}
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button type="submit" form="investor-form" disabled={isPending}>
						{isPending && <IconLoader2 className="animate-spin" />}
						{isEdit ? 'Guardar cambios' : 'Crear inversor'}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
