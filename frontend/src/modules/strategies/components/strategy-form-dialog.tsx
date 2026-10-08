import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import type { Regime } from '@/modules/features/lib/regime';
import { useTimeframesQuery } from '@/modules/market/hooks/use-market-queries';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
import type {
	Strategy,
	StrategyParameters,
	StrategyType,
} from '@/modules/strategies/api/strategies.api';
import {
	useCreateStrategyMutation,
	useUpdateStrategyMutation,
} from '@/modules/strategies/hooks/use-strategies-mutations';
import {
	ANY_REGIME,
	fractionToPercent,
	isRegimeCoherent,
	MAX_RISK_PERCENT,
	percentToFraction,
	REGIME_REQUIRED_OPTIONS,
	regimeCoherenceHint,
	STRATEGY_TYPE_OPTIONS,
} from '@/modules/strategies/lib/strategies-labels';
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

const RULES_PLACEHOLDER =
	'[{"indicator": "rsi_14", "operator": "lt", "value": 30}]';

/** Texto del textarea → lista de reglas. Vacío = sin reglas. */
const rulesField = z
	.string()
	.trim()
	.transform((value, ctx): Record<string, unknown>[] => {
		if (value === '') return [];
		let parsed: unknown;
		try {
			parsed = JSON.parse(value);
		} catch {
			ctx.addIssue({
				code: 'custom',
				message: 'El JSON no es válido. Revisa comillas, comas y corchetes',
			});
			return z.NEVER;
		}
		if (!Array.isArray(parsed)) {
			ctx.addIssue({
				code: 'custom',
				message: 'Debe ser una lista JSON, entre corchetes [ ]',
			});
			return z.NEVER;
		}
		const allObjects = parsed.every(
			(rule) =>
				typeof rule === 'object' && rule !== null && !Array.isArray(rule),
		);
		if (!allObjects) {
			ctx.addIssue({
				code: 'custom',
				message: 'Cada regla debe ser un objeto JSON { }',
			});
			return z.NEVER;
		}
		return parsed as Record<string, unknown>[];
	});

const strategySchema = z
	.object({
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
		strategy_type: requiredSelectField('Elige el tipo'),
		regime_required: requiredSelectField('Elige el régimen'),
		timeframe_code: requiredSelectField('Elige el timeframe'),
		risk_percent: z.coerce
			.number({ message: 'Escribe un número' })
			.gt(0, 'Debe ser mayor que 0')
			.max(
				MAX_RISK_PERCENT,
				'No puede superar el 1 % del capital por operación (regla del 1 %)',
			),
		rules: rulesField,
	})
	.superRefine((values, ctx) => {
		if (!isRegimeCoherent(values.strategy_type, values.regime_required)) {
			ctx.addIssue({
				code: 'custom',
				path: ['regime_required'],
				message: regimeCoherenceHint(values.strategy_type),
			});
		}
	});

type StrategyFormInput = z.input<typeof strategySchema>;
type StrategyFormOutput = z.output<typeof strategySchema>;

type StrategyFormDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	/** `null` = crear; una estrategia = editar. */
	strategy: Strategy | null;
};

function initialValues(strategy: Strategy | null): StrategyFormInput {
	const parameters: StrategyParameters = strategy?.parameters ?? {};
	return {
		name: strategy?.name ?? '',
		version: strategy?.version ?? '1.0.0',
		description: strategy?.description ?? '',
		strategy_type: parameters.strategy_type ?? null,
		// Al editar, `null` en el backend significa "sin restricción"; al crear
		// se obliga a elegir el régimen de forma explícita.
		regime_required: strategy
			? (parameters.regime_required ?? ANY_REGIME)
			: null,
		timeframe_code: parameters.timeframe_code ?? null,
		risk_percent:
			typeof parameters.risk_pct === 'number'
				? fractionToPercent(parameters.risk_pct)
				: MAX_RISK_PERCENT,
		rules: parameters.rules?.length
			? JSON.stringify(parameters.rules, null, 2)
			: '',
	};
}

export function StrategyFormDialog({
	open,
	onOpenChange,
	strategy,
}: StrategyFormDialogProps) {
	const isEdit = !!strategy;
	const timeframesQuery = useTimeframesQuery();
	const createMutation = useCreateStrategyMutation();
	const updateMutation = useUpdateStrategyMutation();
	const isPending = createMutation.isPending || updateMutation.isPending;

	const form = useForm<StrategyFormInput, unknown, StrategyFormOutput>({
		resolver: zodResolver(strategySchema),
		defaultValues: initialValues(null),
	});

	useEffect(() => {
		if (open) form.reset(initialValues(strategy));
	}, [open, strategy, form]);

	// Aviso en vivo del filtro de régimen, antes de enviar.
	const strategyType = useWatch({
		control: form.control,
		name: 'strategy_type',
	});
	const regimeRequired = useWatch({
		control: form.control,
		name: 'regime_required',
	});
	const isIncoherent = !isRegimeCoherent(strategyType, regimeRequired);

	const timeframeOptions = (timeframesQuery.data ?? []).map((timeframe) => ({
		value: timeframe.code,
		label: timeframe.code,
	}));

	function handleSubmit(values: StrategyFormOutput) {
		const parameters: StrategyParameters = {
			// Se conservan claves extra que el formulario no edita.
			...(strategy?.parameters ?? {}),
			strategy_type: values.strategy_type as StrategyType,
			regime_required:
				values.regime_required === ANY_REGIME
					? null
					: (values.regime_required as Regime),
			timeframe_code: values.timeframe_code,
			rules: values.rules,
			risk_pct: percentToFraction(values.risk_percent),
		};
		const callbacks = {
			onSuccess: () => {
				toast.add({
					title: isEdit ? 'Estrategia actualizada' : 'Estrategia creada',
					type: 'success',
				});
				onOpenChange(false);
			},
			onError: (error: unknown) =>
				toast.add({
					title: isEdit
						? 'No pudimos actualizar la estrategia'
						: 'No pudimos crear la estrategia',
					description: getErrorMessage(error),
					type: 'error',
				}),
		};

		if (strategy) {
			// En el PUT, `''` borra la descripción (`null` la dejaría igual).
			updateMutation.mutate(
				{
					id: strategy.id,
					input: {
						name: values.name,
						version: values.version,
						description: values.description,
						parameters,
					},
				},
				callbacks,
			);
		} else {
			createMutation.mutate(
				{
					name: values.name,
					version: values.version,
					description: values.description === '' ? null : values.description,
					parameters,
				},
				callbacks,
			);
		}
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-xl">
				<DialogHeader>
					<DialogTitle>
						{isEdit ? 'Editar estrategia' : 'Nueva estrategia'}
					</DialogTitle>
					<DialogDescription>
						{strategy
							? `${strategy.name} · v${strategy.version}`
							: 'Reglas objetivas que debe cumplir una operación para que el sistema la proponga.'}
					</DialogDescription>
				</DialogHeader>
				<form
					id="strategy-form"
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
											<FieldLabel htmlFor="strategy-name" required>
												Nombre
											</FieldLabel>
											<Input
												{...field}
												id="strategy-name"
												placeholder="EMA Trend Follower"
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
											<FieldLabel htmlFor="strategy-version" required>
												Versión
											</FieldLabel>
											<Input
												{...field}
												id="strategy-version"
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
										<FieldLabel htmlFor="strategy-description">
											Descripción
										</FieldLabel>
										<Input
											{...field}
											id="strategy-description"
											placeholder="Sigue la tendencia usando cruces de EMA"
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<div className="grid gap-4 sm:grid-cols-2">
								<Controller
									name="strategy_type"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="strategy-type" required>
												Tipo
											</FieldLabel>
											<OptionSelect
												id="strategy-type"
												value={field.value}
												onChange={field.onChange}
												options={STRATEGY_TYPE_OPTIONS}
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
								<Controller
									name="regime_required"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid || isIncoherent}>
											<FieldLabel htmlFor="strategy-regime" required>
												Régimen requerido
											</FieldLabel>
											<OptionSelect
												id="strategy-regime"
												value={field.value}
												onChange={field.onChange}
												options={REGIME_REQUIRED_OPTIONS}
												aria-invalid={fieldState.invalid || isIncoherent}
											/>
											{isIncoherent ? (
												<FieldError>
													{regimeCoherenceHint(strategyType)}
												</FieldError>
											) : (
												fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)
											)}
										</Field>
									)}
								/>
								<Controller
									name="timeframe_code"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="strategy-timeframe" required>
												Timeframe
											</FieldLabel>
											<OptionSelect
												id="strategy-timeframe"
												value={field.value}
												onChange={field.onChange}
												options={timeframeOptions}
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
								<Controller
									name="risk_percent"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="strategy-risk" required>
												Riesgo por operación (%)
											</FieldLabel>
											<Input
												{...field}
												value={String(field.value ?? '')}
												id="strategy-risk"
												type="number"
												inputMode="decimal"
												min={0}
												max={MAX_RISK_PERCENT}
												step={0.1}
												placeholder="1"
												aria-invalid={fieldState.invalid}
											/>
											<FieldDescription>
												Máximo 1 % del capital (regla del 1 %).
											</FieldDescription>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							</div>
							<Controller
								name="rules"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="strategy-rules">
											Reglas (JSON)
										</FieldLabel>
										<Textarea
											{...field}
											id="strategy-rules"
											placeholder={RULES_PLACEHOLDER}
											spellCheck={false}
											className="min-h-32 px-3 py-2 font-mono text-xs"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Lista de condiciones con indicador, operador (lt, lte, gt,
											gte, eq) y valor.
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
					<Button type="submit" form="strategy-form" disabled={isPending}>
						{isPending && <IconLoader2 className="animate-spin" />}
						{isEdit ? 'Guardar cambios' : 'Crear estrategia'}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
