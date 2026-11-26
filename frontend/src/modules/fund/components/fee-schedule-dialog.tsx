import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2, IconPlus, IconTrash } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useFieldArray, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { FeeSchedule } from '@/modules/fund/api/fund-payouts.api';
import { useCreateFeeScheduleMutation } from '@/modules/fund/hooks/use-fund-payouts-mutations';
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
	FieldDescription,
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { Textarea } from '@/modules/ui/components/textarea';
import { toast } from '@/modules/ui/components/toast';

const MAX_TIERS = 10;

const pctField = (max: number) =>
	z
		.string()
		.trim()
		.min(1, 'Escribe el %')
		.transform((value) => value.replace(',', '.'))
		.refine(
			(value) =>
				Number.isFinite(Number(value)) &&
				Number(value) >= 0 &&
				Number(value) <= max,
			`Entre 0 y ${max}`,
		);

const scheduleSchema = z
	.object({
		tiers: z
			.array(z.object({ from: pctField(100000), rate: pctField(100) }))
			.min(1)
			.max(MAX_TIERS),
		note: z.string().trim().max(500, 'Máximo 500 caracteres'),
	})
	.superRefine((value, ctx) => {
		value.tiers.forEach((tier, index) => {
			if (index === 0 && Number(tier.from) !== 0) {
				ctx.addIssue({
					code: 'custom',
					path: ['tiers', 0, 'from'],
					message: 'El primer tramo empieza en 0 %',
				});
			}
			const previous = value.tiers[index - 1];
			if (previous && Number(tier.from) <= Number(previous.from)) {
				ctx.addIssue({
					code: 'custom',
					path: ['tiers', index, 'from'],
					message: 'Debe ser mayor que el tramo anterior',
				});
			}
		});
	});

type ScheduleInput = z.input<typeof scheduleSchema>;
type ScheduleOutput = z.output<typeof scheduleSchema>;

function toForm(schedule: FeeSchedule | null): ScheduleInput {
	return {
		tiers: schedule
			? schedule.tiers.map((tier) => ({
					from: tier.from_return_pct,
					rate: tier.rate_pct,
				}))
			: [{ from: '0', rate: '' }],
		note: '',
	};
}

type FeeScheduleDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	current: FeeSchedule | null;
};

/**
 * Nueva versión de la tabla de comisión. No reescribe el pasado: las
 * liquidaciones ya hechas guardan la tabla con la que se cobraron.
 */
export function FeeScheduleDialog({
	open,
	onOpenChange,
	current,
}: FeeScheduleDialogProps) {
	const mutation = useCreateFeeScheduleMutation();
	const form = useForm<ScheduleInput, unknown, ScheduleOutput>({
		resolver: zodResolver(scheduleSchema),
		defaultValues: toForm(current),
	});
	const tiers = useFieldArray({ control: form.control, name: 'tiers' });

	useEffect(() => {
		if (open) form.reset(toForm(current));
	}, [open, current, form]);

	function handleSubmit(values: ScheduleOutput) {
		mutation.mutate(
			{
				tiers: values.tiers.map((tier) => ({
					from_return_pct: tier.from,
					rate_pct: tier.rate,
				})),
				note: values.note || null,
			},
			{
				onSuccess: () => {
					toast.add({ title: 'Tabla de comisión guardada', type: 'success' });
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos guardar la tabla',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle>Tabla de comisión</DialogTitle>
					<DialogDescription>
						Cada tramo cobra su % solo sobre la parte de la ganancia que cae en
						él. Ejemplo: 10 % desde 0 % y 15 % desde 50 %: quien gana 80 % paga
						10 % sobre los primeros 50 puntos y 15 % sobre los otros 30. Rige
						desde la próxima liquidación y todos los participantes la ven.
					</DialogDescription>
				</DialogHeader>
				<form
					id="fee-schedule-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							{tiers.fields.map((item, index) => (
								<div key={item.id} className="flex items-start gap-2">
									<Controller
										name={`tiers.${index}.from`}
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor={`tier-from-${index}`} required>
													Desde (% de ganancia)
												</FieldLabel>
												<Input
													{...field}
													id={`tier-from-${index}`}
													inputMode="decimal"
													readOnly={index === 0}
													aria-invalid={fieldState.invalid}
												/>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
									<Controller
										name={`tiers.${index}.rate`}
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor={`tier-rate-${index}`} required>
													Comisión (%)
												</FieldLabel>
												<Input
													{...field}
													id={`tier-rate-${index}`}
													inputMode="decimal"
													aria-invalid={fieldState.invalid}
												/>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
									<Button
										type="button"
										variant="ghost"
										size="icon"
										className="mt-6 shrink-0"
										aria-label="Quitar tramo"
										disabled={index === 0}
										onClick={() => tiers.remove(index)}
									>
										<IconTrash />
									</Button>
								</div>
							))}
							<Button
								type="button"
								variant="outline"
								className="self-start"
								disabled={tiers.fields.length >= MAX_TIERS}
								onClick={() => tiers.append({ from: '', rate: '' })}
							>
								<IconPlus />
								Añadir tramo
							</Button>
							<Controller
								name="note"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="fee-note">Nota (opcional)</FieldLabel>
										<Textarea
											{...field}
											id="fee-note"
											rows={2}
											maxLength={500}
											placeholder="Ej.: Tabla acordada para 2027."
										/>
										<FieldDescription>
											La ven todos los participantes junto a la tabla.
										</FieldDescription>
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
						form="fee-schedule-form"
						disabled={mutation.isPending}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Guardar tabla
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
