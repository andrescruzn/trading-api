import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { FundSettings } from '@/modules/fund/api/fund.api';
import { useUpdateFundSettingsMutation } from '@/modules/fund/hooks/use-fund-mutations';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import {
	Field,
	FieldDescription,
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

// Mismos límites que el backend (FundSettings / UpdateFundSettingsRequest)
const settingsSchema = z.object({
	min_hold_days: z.coerce
		.number({ message: 'Escribe un número' })
		.int('Debe ser un número entero')
		.min(0, 'Mínimo 0')
		.max(365, 'Máximo 365'),
	deposit_auto_confirm_max: z
		.string()
		.trim()
		.min(1, 'Escribe el monto')
		.transform((value) => value.replace(',', '.'))
		.refine(
			(value) => Number.isFinite(Number(value)) && Number(value) >= 0,
			'Debe ser 0 o más',
		),
	deposit_request_ttl_hours: z.coerce
		.number({ message: 'Escribe un número' })
		.int('Debe ser un número entero')
		.min(1, 'Mínimo 1')
		.max(720, 'Máximo 720'),
});

type SettingsInput = z.input<typeof settingsSchema>;
type SettingsOutput = z.output<typeof settingsSchema>;

type FundSettingsFormProps = {
	settings: FundSettings;
	/** El socio ve los valores sin poder cambiarlos. */
	readOnly: boolean;
};

export function FundSettingsForm({
	settings,
	readOnly,
}: FundSettingsFormProps) {
	const mutation = useUpdateFundSettingsMutation();
	const form = useForm<SettingsInput, unknown, SettingsOutput>({
		resolver: zodResolver(settingsSchema),
		defaultValues: {
			min_hold_days: settings.min_hold_days,
			deposit_auto_confirm_max: settings.deposit_auto_confirm_max,
			deposit_request_ttl_hours: settings.deposit_request_ttl_hours,
		},
	});

	useEffect(() => {
		form.reset({
			min_hold_days: settings.min_hold_days,
			deposit_auto_confirm_max: settings.deposit_auto_confirm_max,
			deposit_request_ttl_hours: settings.deposit_request_ttl_hours,
		});
	}, [settings, form]);

	function handleSubmit(values: SettingsOutput) {
		mutation.mutate(values, {
			onSuccess: () =>
				toast.add({ title: 'Ajustes guardados', type: 'success' }),
			onError: (error) =>
				toast.add({
					title: 'No pudimos guardar los ajustes',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Card>
			<CardHeader>
				<CardTitle>Reglas del fondo</CardTitle>
				<CardDescription>
					Aplican a todos: propietarios, socios e inversores.
				</CardDescription>
			</CardHeader>
			<form onSubmit={form.handleSubmit(handleSubmit)} noValidate>
				<CardContent>
					<FieldGroup className="grid gap-4 md:grid-cols-3">
						<Controller
							name="min_hold_days"
							control={form.control}
							render={({ field, fieldState }) => (
								<Field data-invalid={fieldState.invalid}>
									<FieldLabel htmlFor="settings-hold-days">
										Permanencia mínima (días)
									</FieldLabel>
									<Input
										{...field}
										value={String(field.value ?? '')}
										id="settings-hold-days"
										inputMode="numeric"
										disabled={readOnly}
										aria-invalid={fieldState.invalid}
									/>
									<FieldDescription>
										Lo depositado debe estar este tiempo en un agente antes de
										poder retirarlo.
									</FieldDescription>
									{fieldState.invalid && (
										<FieldError errors={[fieldState.error]} />
									)}
								</Field>
							)}
						/>
						<Controller
							name="deposit_auto_confirm_max"
							control={form.control}
							render={({ field, fieldState }) => (
								<Field data-invalid={fieldState.invalid}>
									<FieldLabel htmlFor="settings-auto-max">
										Confirmación automática hasta (USDT)
									</FieldLabel>
									<Input
										{...field}
										id="settings-auto-max"
										inputMode="decimal"
										disabled={readOnly}
										aria-invalid={fieldState.invalid}
									/>
									<FieldDescription>
										Un depósito verificado hasta este monto se acredita solo;
										uno mayor lo revisa un super admin. 0 = revisar todos.
									</FieldDescription>
									{fieldState.invalid && (
										<FieldError errors={[fieldState.error]} />
									)}
								</Field>
							)}
						/>
						<Controller
							name="deposit_request_ttl_hours"
							control={form.control}
							render={({ field, fieldState }) => (
								<Field data-invalid={fieldState.invalid}>
									<FieldLabel htmlFor="settings-ttl">
										Vencimiento de solicitudes (horas)
									</FieldLabel>
									<Input
										{...field}
										value={String(field.value ?? '')}
										id="settings-ttl"
										inputMode="numeric"
										disabled={readOnly}
										aria-invalid={fieldState.invalid}
									/>
									<FieldDescription>
										Si el txid no aparece en el exchange en este tiempo, la
										solicitud vence.
									</FieldDescription>
									{fieldState.invalid && (
										<FieldError errors={[fieldState.error]} />
									)}
								</Field>
							)}
						/>
					</FieldGroup>
				</CardContent>
				{!readOnly && (
					<CardFooter className="justify-end">
						<Button type="submit" disabled={mutation.isPending}>
							{mutation.isPending && <IconLoader2 className="animate-spin" />}
							Guardar reglas
						</Button>
					</CardFooter>
				)}
			</form>
		</Card>
	);
}
