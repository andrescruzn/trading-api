import { zodResolver } from '@hookform/resolvers/zod';
import {
	IconArrowLeft,
	IconArrowRight,
	IconLoader2,
	IconRocket,
} from '@tabler/icons-react';
import { getRouteApi, Link, useNavigate } from '@tanstack/react-router';
import { type ReactNode, useMemo, useState } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { BotMode } from '@/modules/bots/api/bots.api';
import { MoneyStep } from '@/modules/bots/components/agent-wizard/money-step';
import { StrategyStep } from '@/modules/bots/components/agent-wizard/strategy-step';
import { SymbolStep } from '@/modules/bots/components/agent-wizard/symbol-step';
import { BotModeBadge } from '@/modules/bots/components/bot-badges';
import { ExecutionModePicker } from '@/modules/bots/components/execution-mode-picker';
import {
	useCreateBotMutation,
	useTransitionBotMutation,
} from '@/modules/bots/hooks/use-bots-mutations';
import {
	defaultAgentName,
	strategyRiskFraction,
	strategyTimeframe,
} from '@/modules/bots/lib/agent-wizard';
import { useFeatureSetsQuery } from '@/modules/features/hooks/use-features-queries';
import { INDICATOR_GROUP_LABELS } from '@/modules/features/lib/features-labels';
import {
	useSymbolsQuery,
	useTimeframesQuery,
} from '@/modules/market/hooks/use-market-queries';
import { isPerpetualSymbol } from '@/modules/market/lib/market-labels';
import { Stepper } from '@/modules/shared/components/stepper';
import { formatPercent, formatPrice } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
import { useStrategiesQuery } from '@/modules/strategies/hooks/use-strategies-queries';
import { strategyTypeLabel } from '@/modules/strategies/lib/strategies-labels';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { Checkbox } from '@/modules/ui/components/checkbox';
import {
	Field,
	FieldDescription,
	FieldError,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

// Mismo tope que el backend (MAX_DEMO_CAPITAL).
const MAX_DEMO_CAPITAL = 1_000_000_000;

const agentSchema = z.object({
	symbol_id: requiredSelectField('Elige qué quieres operar'),
	strategy_id: requiredSelectField('Elige una estrategia'),
	feature_set_id: requiredSelectField('Elige un conjunto de indicadores'),
	// Solo los agentes demo llevan monto (ver `agentSchemaFor`).
	demo_capital: z.string(),
	name: z
		.string()
		.trim()
		.min(1, 'Escribe un nombre para el agente')
		.max(80, 'Máximo 80 caracteres'),
	start_now: z.boolean(),
	execution_mode: z.enum(['manual', 'approval', 'auto']),
});

type AgentFormInput = z.input<typeof agentSchema>;
type AgentFormValues = z.output<typeof agentSchema>;

/** El demo exige un monto válido; el real opera con la billetera y no lleva monto. */
function agentSchemaFor(mode: BotMode) {
	if (mode === 'live') return agentSchema;
	return agentSchema.extend({
		demo_capital: z
			.string()
			.trim()
			.refine(
				(value) => Number(value) > 0 && Number(value) <= MAX_DEMO_CAPITAL,
				'Escribe un monto mayor que 0 y de hasta 1.000.000.000',
			),
	});
}

const STEPS = [
	{
		title: '¿Qué quieres operar?',
		description:
			'Elige el símbolo. El agente descarga sus velas solo mientras está activo.',
		fields: ['symbol_id'],
	},
	{
		title: '¿Cómo opera?',
		description:
			'La estrategia define cuándo entrar, en qué timeframe y cuánto arriesgar.',
		fields: ['strategy_id', 'feature_set_id'],
	},
	{
		title: '¿Con qué dinero?',
		description:
			'Un agente real opera la billetera de Binance; uno demo, un monto simulado.',
		fields: ['demo_capital'],
	},
	{
		title: 'Revisa y crea',
		description: 'Ponle un nombre y confirma la configuración.',
		fields: ['name'],
	},
] as const satisfies {
	title: string;
	description: string;
	fields: (keyof AgentFormInput)[];
}[];

function SummaryRow({
	label,
	children,
}: {
	label: string;
	children: ReactNode;
}) {
	return (
		<div className="flex flex-col gap-1 py-3 sm:flex-row sm:items-baseline sm:justify-between sm:gap-6">
			<dt className="text-sm text-muted-foreground">{label}</dt>
			<dd className="text-sm font-medium sm:text-right">{children}</dd>
		</div>
	);
}

const routeApi = getRouteApi('/_app/agents/new');

export function AgentNewPage() {
	const search = routeApi.useSearch();
	const mode: BotMode = search.mode ?? 'live';
	const isDemo = mode === 'paper';
	usePageBreadcrumb([
		isDemo
			? { label: 'Agentes demo', href: '/demo-agents' }
			: { label: 'Inicio', href: '/dashboard' },
		{ label: isDemo ? 'Nuevo agente demo' : 'Nuevo agente real' },
	]);
	const navigate = useNavigate();
	const symbolsQuery = useSymbolsQuery({ is_active: true });
	const timeframesQuery = useTimeframesQuery();
	const strategiesQuery = useStrategiesQuery();
	const featureSetsQuery = useFeatureSetsQuery();
	const createMutation = useCreateBotMutation();
	const transitionMutation = useTransitionBotMutation();
	const [step, setStep] = useState(0);
	// El nombre sugerido solo se aplica hasta que la persona lo edita.
	const [nameTouched, setNameTouched] = useState(false);

	const schema = useMemo(() => agentSchemaFor(mode), [mode]);
	const form = useForm<AgentFormInput, unknown, AgentFormValues>({
		resolver: zodResolver(schema),
		defaultValues: {
			symbol_id: search.symbol_id ? String(search.symbol_id) : null,
			strategy_id: null,
			feature_set_id: null,
			demo_capital: isDemo ? '10000' : '',
			name: '',
			start_now: true,
			execution_mode: 'manual',
		},
	});
	const values = useWatch({ control: form.control });

	// Solo símbolos cuyas velas se descargan solas: si no, el agente nunca
	// tendría datos para analizar.
	const symbols = symbolsQuery.data?.filter((item) => item.supports_auto_fetch);
	const symbol = symbols?.find((item) => String(item.id) === values.symbol_id);
	// Un perpetuo real opera en la billetera de Futuros: el paso del dinero lo explica.
	const perpetual = isPerpetualSymbol(symbol?.symbol);
	const currency = symbol?.quote_asset ?? 'USDT';

	const strategy = strategiesQuery.data?.find(
		(item) => String(item.id) === values.strategy_id,
	);
	const featureSet = featureSetsQuery.data?.find(
		(item) => String(item.id) === values.feature_set_id,
	);
	const timeframe = strategy
		? strategyTimeframe(strategy, timeframesQuery.data)
		: null;
	const riskFraction = strategy ? strategyRiskFraction(strategy) : null;
	const isSubmitting = createMutation.isPending || transitionMutation.isPending;

	function suggestName(nextSymbol = symbol, nextStrategy = strategy) {
		if (nameTouched) return;
		form.setValue('name', defaultAgentName(nextSymbol, nextStrategy));
	}

	async function goNext() {
		const valid = await form.trigger([...STEPS[step].fields]);
		if (!valid) return;
		if (step === 1 && !timeframe) {
			toast.add({
				title: 'Falta el timeframe',
				description:
					'La estrategia no declara un timeframe disponible. Elige otra.',
				type: 'error',
			});
			return;
		}
		setStep((current) => Math.min(current + 1, STEPS.length - 1));
	}

	function handleSubmit(formValues: AgentFormValues) {
		if (!timeframe || riskFraction === null) return;
		createMutation.mutate(
			{
				name: formValues.name,
				symbol_id: Number(formValues.symbol_id),
				strategy_id: Number(formValues.strategy_id),
				feature_set_id: Number(formValues.feature_set_id),
				timeframe_id: timeframe.id,
				mode,
				demo_capital: isDemo ? Number(formValues.demo_capital) : undefined,
				risk_params: { risk_pct: riskFraction },
				execution_mode: formValues.execution_mode,
			},
			{
				onSuccess: (bot) => {
					const openDetail = () =>
						navigate({
							to: '/agents/$agentId',
							params: { agentId: String(bot.id) },
						});
					if (!formValues.start_now) {
						toast.add({ title: 'Agente creado', type: 'success' });
						openDetail();
						return;
					}
					transitionMutation.mutate(
						{ id: bot.id, transition: 'start' },
						{
							onSuccess: () =>
								toast.add({
									title: 'Agente creado e iniciado',
									description:
										'Está descargando velas y calculando indicadores.',
									type: 'success',
								}),
							onError: (error) =>
								toast.add({
									title: 'Agente creado, pero no pudimos iniciarlo',
									description: getErrorMessage(error),
									type: 'error',
								}),
							onSettled: openDetail,
						},
					);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos crear el agente',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	const stepperSteps = [
		{ title: 'Qué operar', summary: symbol?.symbol },
		{ title: 'Cómo opera', summary: strategy?.name },
		{
			title: 'Con qué dinero',
			summary: isDemo
				? values.demo_capital
					? `${formatPrice(values.demo_capital)} simulados`
					: undefined
				: 'Billetera de Binance',
		},
		{ title: 'Revisar' },
	];
	const current = STEPS[step];
	const fieldError = (name: keyof AgentFormInput) =>
		form.formState.errors[name]?.message;

	return (
		<div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
			<div className="flex flex-col gap-1">
				<h1 className="text-xl font-semibold">
					{isDemo ? 'Nuevo agente demo' : 'Nuevo agente real'}
				</h1>
				<p className="text-sm text-muted-foreground">
					Un agente vigila un símbolo, aplica una estrategia y le pide a la IA
					que confirme cada operación. Solo propone las que cumplen la regla del
					1 % y un riesgo/beneficio de al menos 2:1.
				</p>
			</div>

			<Stepper steps={stepperSteps} current={step} onStepClick={setStep} />

			<form
				id="agent-form"
				noValidate
				onSubmit={(event) => {
					// Enter en un campo de un paso intermedio avanza en vez de enviar.
					if (step < STEPS.length - 1) {
						event.preventDefault();
						void goNext();
						return;
					}
					void form.handleSubmit(handleSubmit)(event);
				}}
				className="contents"
			>
				<Card key={step} className="animate-in fade-in slide-in-from-bottom-1">
					<CardHeader>
						<CardTitle>{current.title}</CardTitle>
						<CardDescription>{current.description}</CardDescription>
					</CardHeader>
					<CardContent className="flex flex-col gap-4">
						{step === 0 && (
							<Controller
								name="symbol_id"
								control={form.control}
								render={({ field }) => (
									<SymbolStep
										symbols={symbols}
										isLoading={symbolsQuery.isLoading}
										value={field.value}
										onChange={(value) => {
											field.onChange(value);
											suggestName(
												symbols?.find((item) => String(item.id) === value),
												strategy,
											);
										}}
									/>
								)}
							/>
						)}

						{step === 1 && (
							<StrategyStep
								strategies={strategiesQuery.data}
								featureSets={featureSetsQuery.data}
								isLoading={
									strategiesQuery.isLoading || featureSetsQuery.isLoading
								}
								strategyId={values.strategy_id ?? null}
								featureSetId={values.feature_set_id ?? null}
								onStrategyChange={(nextStrategy, recommended) => {
									form.setValue('strategy_id', String(nextStrategy.id), {
										shouldValidate: true,
									});
									form.setValue(
										'feature_set_id',
										recommended ? String(recommended.id) : null,
									);
									suggestName(symbol, nextStrategy);
								}}
								onFeatureSetChange={(value) =>
									form.setValue('feature_set_id', value, {
										shouldValidate: true,
									})
								}
							/>
						)}

						{step === 2 && (
							<Controller
								name="demo_capital"
								control={form.control}
								render={({ field, fieldState }) => (
									<MoneyStep
										mode={mode}
										currency={currency}
										perpetual={perpetual}
										capital={field.value}
										onCapitalChange={field.onChange}
										capitalError={fieldState.error?.message}
									/>
								)}
							/>
						)}

						{step === 3 && (
							<div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
								<dl className="divide-y rounded-xl border px-4">
									<SummaryRow label="Opera">
										<span className="font-mono">
											{symbol?.symbol ?? '—'}
											{timeframe ? ` · ${timeframe.code}` : ''}
										</span>
									</SummaryRow>
									<SummaryRow label="Estrategia">
										{strategy
											? `${strategy.name} v${strategy.version} · ${strategyTypeLabel(strategy.parameters.strategy_type)}`
											: '—'}
									</SummaryRow>
									<SummaryRow label="Indicadores">
										{featureSet
											? `${featureSet.name}: ${featureSet.indicators
													.map(
														(group) => INDICATOR_GROUP_LABELS[group] ?? group,
													)
													.join(', ')}`
											: '—'}
									</SummaryRow>
									<SummaryRow label="Dinero">
										<span className="inline-flex items-center gap-2">
											{isDemo
												? `${formatPrice(values.demo_capital)} simulados`
												: 'Billetera de Binance'}
											<BotModeBadge mode={mode} />
										</span>
									</SummaryRow>
									<SummaryRow label="Riesgo por operación">
										{formatPercent(riskFraction, 1)} del capital
										<span className="block text-xs font-normal text-muted-foreground">
											Lo define la estrategia (máximo 1 %).
										</span>
									</SummaryRow>
									<div className="flex flex-col gap-3 py-3">
										<dt className="text-sm text-muted-foreground">
											Cuando la IA aprueba una operación
										</dt>
										<dd>
											<Controller
												name="execution_mode"
												control={form.control}
												render={({ field }) => (
													<ExecutionModePicker
														value={field.value}
														onChange={field.onChange}
														accountMode={mode}
													/>
												)}
											/>
										</dd>
									</div>
								</dl>

								<div className="flex flex-col gap-5">
									<Controller
										name="name"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="agent-name" required>
													Nombre del agente
												</FieldLabel>
												<Input
													{...field}
													id="agent-name"
													maxLength={80}
													placeholder="BTC/USDT · Tendencia"
													aria-invalid={fieldState.invalid}
													onChange={(event) => {
														setNameTouched(true);
														field.onChange(event);
													}}
												/>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
									<Controller
										name="start_now"
										control={form.control}
										render={({ field }) => (
											<Field orientation="horizontal">
												<Checkbox
													id="agent-start-now"
													checked={field.value}
													onCheckedChange={(checked) => field.onChange(checked)}
												/>
												<div className="flex flex-col gap-0.5">
													<FieldLabel htmlFor="agent-start-now">
														Iniciarlo al crear
													</FieldLabel>
													<FieldDescription>
														Empieza a descargar velas y calcular indicadores de
														inmediato.
													</FieldDescription>
												</div>
											</Field>
										)}
									/>
								</div>
							</div>
						)}

						{/* Errores de los campos que no tienen un input propio */}
						{STEPS[step].fields
							.filter((name) => name !== 'name' && name !== 'demo_capital')
							.map((name) =>
								fieldError(name) ? (
									<p key={name} className="text-sm text-destructive">
										{fieldError(name)}
									</p>
								) : null,
							)}
					</CardContent>
					<CardFooter className="justify-between gap-2 border-t">
						{step === 0 ? (
							<Button
								variant="ghost"
								render={<Link to={isDemo ? '/demo-agents' : '/dashboard'} />}
							>
								Cancelar
							</Button>
						) : (
							<Button
								variant="ghost"
								onClick={() => setStep((value) => value - 1)}
								disabled={isSubmitting}
							>
								<IconArrowLeft />
								Atrás
							</Button>
						)}
						{step < STEPS.length - 1 ? (
							<Button onClick={goNext}>
								Continuar
								<IconArrowRight />
							</Button>
						) : (
							<Button type="submit" form="agent-form" disabled={isSubmitting}>
								{isSubmitting ? (
									<IconLoader2 className="animate-spin" />
								) : (
									<IconRocket />
								)}
								Crear agente
							</Button>
						)}
					</CardFooter>
				</Card>
			</form>
		</div>
	);
}
