import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { useCreateFeatureSetMutation } from '@/modules/features/hooks/use-features-mutations';
import { jsonObjectError } from '@/modules/features/lib/features-labels';
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

const SPEC_PLACEHOLDER =
	'{"rsi": true, "ema": [20, 50, 200], "macd": true, "atr": true, "bbands": true}';

const featureSetSchema = z.object({
	name: z
		.string()
		.trim()
		.min(1, 'Escribe el nombre')
		.max(120, 'Máximo 120 caracteres'),
	version: z
		.string()
		.trim()
		.min(1, 'Escribe la versión')
		.max(32, 'Máximo 32 caracteres'),
	description: z.string().trim(),
	// Se valida como texto y se convierte a objeto al enviar.
	spec: z
		.string()
		.trim()
		.min(1, 'Escribe la configuración en JSON')
		.superRefine((value, ctx) => {
			const message = jsonObjectError(value);
			if (message) ctx.addIssue({ code: 'custom', message });
		}),
});

type FeatureSetValues = z.infer<typeof featureSetSchema>;

const EMPTY_VALUES: FeatureSetValues = {
	name: '',
	version: '1.0.0',
	description: '',
	spec: '',
};

type FeatureSetFormDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
};

export function FeatureSetFormDialog({
	open,
	onOpenChange,
}: FeatureSetFormDialogProps) {
	const createMutation = useCreateFeatureSetMutation();

	const form = useForm<FeatureSetValues>({
		resolver: zodResolver(featureSetSchema),
		defaultValues: EMPTY_VALUES,
	});

	useEffect(() => {
		if (open) form.reset(EMPTY_VALUES);
	}, [open, form]);

	function handleSubmit(values: FeatureSetValues) {
		createMutation.mutate(
			{
				name: values.name,
				version: values.version,
				description: values.description === '' ? null : values.description,
				spec: JSON.parse(values.spec) as Record<string, unknown>,
			},
			{
				onSuccess: () => {
					toast.add({ title: 'Feature set creado', type: 'success' });
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos crear el feature set',
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
					<DialogTitle>Nuevo feature set</DialogTitle>
					<DialogDescription>
						Conjunto de indicadores que se calcula para cada vela.
					</DialogDescription>
				</DialogHeader>
				<form
					id="feature-set-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<div className="grid gap-4 sm:grid-cols-[1fr_8rem]">
								<Controller
									name="name"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="feature-set-name" required>
												Nombre
											</FieldLabel>
											<Input
												{...field}
												id="feature-set-name"
												placeholder="default"
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
								<Controller
									name="version"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="feature-set-version" required>
												Versión
											</FieldLabel>
											<Input
												{...field}
												id="feature-set-version"
												placeholder="1.0.0"
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							</div>
							<Controller
								name="description"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="feature-set-description">
											Descripción
										</FieldLabel>
										<Input
											{...field}
											id="feature-set-description"
											placeholder="Indicadores base para tendencia y rango"
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="spec"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="feature-set-spec" required>
											Configuración (JSON)
										</FieldLabel>
										<Textarea
											{...field}
											id="feature-set-spec"
											placeholder={SPEC_PLACEHOLDER}
											spellCheck={false}
											className="min-h-32 px-3 py-2 font-mono text-xs"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Objeto JSON con los indicadores y sus parámetros.
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
						form="feature-set-form"
						disabled={createMutation.isPending}
					>
						{createMutation.isPending && (
							<IconLoader2 className="animate-spin" />
						)}
						Crear feature set
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
