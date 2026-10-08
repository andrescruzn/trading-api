import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import type {
	AlertRule,
	AlertRuleSpec,
	AlertRuleType,
	PnlPeriod,
	PriceOperator,
	SignalActionFilter,
} from '@/modules/alerts/api/alerts.api';
import {
	useCreateAlertRuleMutation,
	useUpdateAlertRuleMutation,
} from '@/modules/alerts/hooks/use-alerts-mutations';
import {
	botOptions,
	PNL_PERIOD_OPTIONS,
	PRICE_OPERATOR_OPTIONS,
	RULE_TYPE_DESCRIPTIONS,
	RULE_TYPE_OPTIONS,
	SIGNAL_ACTION_OPTIONS,
} from '@/modules/alerts/lib/alerts-labels';
import { useMyBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { useSymbolsQuery } from '@/modules/market/hooks/use-market-queries';
import { symbolOptions } from '@/modules/market/lib/market-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
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
	FieldLegend,
	FieldSet,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

// Valor del select de bot cuando la regla aplica a cualquiera de tus bots.
const ANY_BOT = 'any';

const isNumber = (value: string) => value !== '' && Number.isFinite(Number(value));

// Los campos de la condición dependen del tipo: se guardan como texto en el
// formulario y solo se validan los del tipo elegido (`superRefine`).
const ruleSchema = z
	.object({
		name: z
			.string()
			.trim()
			.min(1, 'Escribe el nombre')
			.max(255, 'Máximo 255 caracteres'),
		rule_type: requiredSelectField('Elige el tipo de regla'),
		bot_id: z.string().nullable(),
		signal_action: z.string(),
		price_symbol_id: z.string().nullable(),
		price_operator: z.string(),
		price_threshold: z.string().trim(),
		pnl_threshold: z.string().trim(),
		pnl_period: z.string(),
		drawdown_threshold: z.string().trim(),
		email: z.boolean(),
		telegram: z.boolean(),
		desktop: z.boolean(),
		webhook: z
			.string()
			.trim()
			.refine(
				(value) => value === '' || /^https?:\/\/\S+$/.test(value),
				'Escribe una URL que empiece por http:// o https://',
			),
	})
	.superRefine((values, ctx) => {
		const requireField = (path: string, valid: boolean, message: string) => {
			if (!valid) ctx.addIssue({ code: 'custom', path: [path], message });
		};
		if (values.rule_type === 'price') {
			requireField('price_symbol_id', !!values.price_symbol_id, 'Elige el símbolo');
			requireField(
				'price_threshold',
				isNumber(values.price_threshold) && Number(values.price_threshold) > 0,
				'Debe ser un número mayor que 0',
			);
		}
		if (values.rule_type === 'pnl') {
			requireField('pnl_threshold', isNumber(values.pnl_threshold), 'Escribe un número, p. ej. -5');
		}
		if (values.rule_type === 'drawdown') {
			requireField(
				'drawdown_threshold',
				isNumber(values.drawdown_threshold) && Number(values.drawdown_threshold) > 0,
				'Debe ser un número mayor que 0',
			);
		}
	});

type RuleFormInput = z.input<typeof ruleSchema>;
type RuleFormOutput = z.output<typeof ruleSchema>;

const EMPTY_VALUES: RuleFormInput = {
	name: '',
	rule_type: 'signal',
	bot_id: ANY_BOT,
	signal_action: 'any',
	price_symbol_id: null,
	price_operator: 'lt',
	price_threshold: '',
	pnl_threshold: '',
	pnl_period: 'daily',
	drawdown_threshold: '',
	email: false,
	telegram: false,
	desktop: false,
	webhook: '',
};

function toText(value: number | string | null | undefined): string {
	return value === null || value === undefined ? '' : String(value);
}

/** Arma el `rule_spec` con la misma forma que espera el evaluador del backend. */
function buildRuleSpec(values: RuleFormOutput): AlertRuleSpec {
	switch (values.rule_type as AlertRuleType) {
		case 'signal':
			return { action: values.signal_action as SignalActionFilter };
		case 'price':
			return {
				symbol_id: Number(values.price_symbol_id),
				operator: values.price_operator as PriceOperator,
				threshold: Number(values.price_threshold),
			};
		case 'pnl':
			return {
				threshold: Number(values.pnl_threshold),
				period: values.pnl_period as PnlPeriod,
			};
		case 'drawdown':
			return { threshold: Number(values.drawdown_threshold) };
		default:
			return {};
	}
}

type AlertRuleFormDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	/** `null` = crear; una regla = editar (tipo y bot no se cambian). */
	rule: AlertRule | null;
};

export function AlertRuleFormDialog({
	open,
	onOpenChange,
	rule,
}: AlertRuleFormDialogProps) {
	const isEdit = !!rule;
	const botsQuery = useMyBotsQuery();
	// Misma consulta (sin filtros) que la tabla de la página: ya llega en caché
	// y el select de símbolo no arranca vacío al editar.
	const symbolsQuery = useSymbolsQuery();
	const activeSymbols = symbolsQuery.data?.filter((symbol) => symbol.is_active);
	const createMutation = useCreateAlertRuleMutation();
	const updateMutation = useUpdateAlertRuleMutation();
	const isPending = createMutation.isPending || updateMutation.isPending;

	const form = useForm<RuleFormInput, unknown, RuleFormOutput>({
		resolver: zodResolver(ruleSchema),
		defaultValues: EMPTY_VALUES,
	});
	const ruleType = useWatch({ control: form.control, name: 'rule_type' });

	useEffect(() => {
		if (!open) return;
		if (!rule) {
			form.reset(EMPTY_VALUES);
			return;
		}
		const spec = rule.rule_spec ?? {};
		const channels = rule.channels ?? {};
		form.reset({
			name: rule.name,
			rule_type: rule.rule_type,
			bot_id: rule.bot_id ? String(rule.bot_id) : ANY_BOT,
			signal_action: spec.action ?? 'any',
			price_symbol_id: spec.symbol_id ? String(spec.symbol_id) : null,
			price_operator: spec.operator ?? 'lt',
			price_threshold: rule.rule_type === 'price' ? toText(spec.threshold) : '',
			pnl_threshold: rule.rule_type === 'pnl' ? toText(spec.threshold) : '',
			pnl_period: spec.period ?? 'daily',
			drawdown_threshold: rule.rule_type === 'drawdown' ? toText(spec.threshold) : '',
			email: !!channels.email,
			telegram: !!channels.telegram,
			desktop: !!channels.desktop,
			webhook: typeof channels.webhook === 'string' ? channels.webhook : '',
		});
	}, [open, rule, form]);

	function handleSubmit(values: RuleFormOutput) {
		const ruleSpec = buildRuleSpec(values);
		const channels = {
			email: values.email,
			telegram: values.telegram,
			desktop: values.desktop,
			webhook: values.webhook || (false as const),
		};
		const callbacks = {
			onSuccess: () => {
				toast.add({
					title: isEdit ? 'Regla actualizada' : 'Regla creada',
					type: 'success',
				});
				onOpenChange(false);
			},
			onError: (error: unknown) =>
				toast.add({
					title: isEdit
						? 'No pudimos actualizar la regla'
						: 'No pudimos crear la regla',
					description: getErrorMessage(error),
					type: 'error',
				}),
		};

		if (rule) {
			updateMutation.mutate(
				{ id: rule.id, input: { name: values.name, rule_spec: ruleSpec, channels } },
				callbacks,
			);
		} else {
			createMutation.mutate(
				{
					name: values.name,
					rule_type: values.rule_type as AlertRuleType,
					rule_spec: ruleSpec,
					channels,
					bot_id:
						values.bot_id && values.bot_id !== ANY_BOT ? Number(values.bot_id) : null,
				},
				callbacks,
			);
		}
	}

	const typeDescription = ruleType
		? RULE_TYPE_DESCRIPTIONS[ruleType as AlertRuleType]
		: undefined;

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle>{isEdit ? 'Editar regla' : 'Nueva regla de alerta'}</DialogTitle>
					<DialogDescription>
						Define qué evento te avisa y por qué canales llega el aviso.
					</DialogDescription>
				</DialogHeader>
				<form
					id="alert-rule-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="name"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="alert-rule-name" required>
											Nombre
										</FieldLabel>
										<Input
											{...field}
											id="alert-rule-name"
											placeholder="Compras del bot principal"
											maxLength={255}
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
									name="rule_type"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="alert-rule-type" required>
												Tipo
											</FieldLabel>
											<OptionSelect
												id="alert-rule-type"
												value={field.value}
												onChange={field.onChange}
												options={RULE_TYPE_OPTIONS}
												disabled={isEdit}
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
								<Controller
									name="bot_id"
									control={form.control}
									render={({ field }) => (
										<Field>
											<FieldLabel htmlFor="alert-rule-bot">Bot</FieldLabel>
											<OptionSelect
												id="alert-rule-bot"
												value={field.value}
												onChange={field.onChange}
												options={[
													{ value: ANY_BOT, label: 'Cualquier bot' },
													...botOptions(botsQuery.data, symbolsQuery.data),
												]}
												disabled={isEdit}
											/>
										</Field>
									)}
								/>
							</div>
							{(typeDescription || isEdit) && (
								<FieldDescription>
									{typeDescription}
									{isEdit && ' El tipo y el bot no se pueden cambiar.'}
								</FieldDescription>
							)}

							{ruleType === 'signal' && (
								<Controller
									name="signal_action"
									control={form.control}
									render={({ field }) => (
										<Field>
											<FieldLabel htmlFor="alert-rule-action">
												Señal a vigilar
											</FieldLabel>
											<OptionSelect
												id="alert-rule-action"
												value={field.value}
												onChange={field.onChange}
												options={SIGNAL_ACTION_OPTIONS}
											/>
										</Field>
									)}
								/>
							)}

							{ruleType === 'price' && (
								<div className="grid gap-4 sm:grid-cols-3">
									<Controller
										name="price_symbol_id"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="alert-rule-symbol" required>
													Símbolo
												</FieldLabel>
												<OptionSelect
													id="alert-rule-symbol"
													value={field.value}
													onChange={field.onChange}
													options={symbolOptions(activeSymbols)}
													placeholder="Elige"
													aria-invalid={fieldState.invalid}
												/>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
									<Controller
										name="price_operator"
										control={form.control}
										render={({ field }) => (
											<Field>
												<FieldLabel htmlFor="alert-rule-operator">Condición</FieldLabel>
												<OptionSelect
													id="alert-rule-operator"
													value={field.value}
													onChange={field.onChange}
													options={PRICE_OPERATOR_OPTIONS}
												/>
											</Field>
										)}
									/>
									<Controller
										name="price_threshold"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="alert-rule-price" required>
													Precio
												</FieldLabel>
												<Input
													{...field}
													id="alert-rule-price"
													type="number"
													inputMode="decimal"
													step="any"
													placeholder="80000"
													aria-invalid={fieldState.invalid}
												/>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
								</div>
							)}

							{ruleType === 'pnl' && (
								<div className="grid gap-4 sm:grid-cols-2">
									<Controller
										name="pnl_threshold"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="alert-rule-pnl" required>
													Umbral (%)
												</FieldLabel>
												<Input
													{...field}
													id="alert-rule-pnl"
													type="number"
													inputMode="decimal"
													step="any"
													placeholder="-5"
													aria-invalid={fieldState.invalid}
												/>
												<FieldDescription>
													Negativo para pérdidas, positivo para ganancias.
												</FieldDescription>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
									<Controller
										name="pnl_period"
										control={form.control}
										render={({ field }) => (
											<Field>
												<FieldLabel htmlFor="alert-rule-period">Período</FieldLabel>
												<OptionSelect
													id="alert-rule-period"
													value={field.value}
													onChange={field.onChange}
													options={PNL_PERIOD_OPTIONS}
												/>
											</Field>
										)}
									/>
								</div>
							)}

							{ruleType === 'drawdown' && (
								<Controller
									name="drawdown_threshold"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="alert-rule-drawdown" required>
												Drawdown máximo (%)
											</FieldLabel>
											<Input
												{...field}
												id="alert-rule-drawdown"
												type="number"
												inputMode="decimal"
												step="any"
												placeholder="10"
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							)}

							<FieldSet>
								<FieldLegend variant="label">Canales</FieldLegend>
								<div className="flex flex-wrap gap-x-6 gap-y-3">
									{(
										[
											['email', 'Correo'],
											['telegram', 'Telegram'],
											['desktop', 'Escritorio'],
										] as const
									).map(([name, label]) => (
										<Controller
											key={name}
											name={name}
											control={form.control}
											render={({ field }) => (
												<Field orientation="horizontal" className="w-auto">
													<Checkbox
														id={`alert-rule-${name}`}
														checked={field.value}
														onCheckedChange={(checked) => field.onChange(checked)}
													/>
													<FieldLabel htmlFor={`alert-rule-${name}`}>{label}</FieldLabel>
												</Field>
											)}
										/>
									))}
								</div>
								<Controller
									name="webhook"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="alert-rule-webhook">URL de webhook</FieldLabel>
											<Input
												{...field}
												id="alert-rule-webhook"
												type="url"
												inputMode="url"
												placeholder="https://hooks.ejemplo.com/trading"
												aria-invalid={fieldState.invalid}
											/>
											<FieldDescription>
												Opcional. Sin canales, la alerta solo queda en tu historial.
											</FieldDescription>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							</FieldSet>
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button type="submit" form="alert-rule-form" disabled={isPending}>
						{isPending && <IconLoader2 className="animate-spin" />}
						{isEdit ? 'Guardar cambios' : 'Crear regla'}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
