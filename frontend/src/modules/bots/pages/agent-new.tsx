import { zodResolver } from '@hookform/resolvers/zod';
import {
	IconAlertTriangle,
	IconArrowLeft,
	IconArrowRight,
	IconLoader2,
	IconRocket,
} from '@tabler/icons-react';
import { getRouteApi, Link, useNavigate } from '@tanstack/react-router';
import { type ReactNode, useState } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import type { BotMode } from '@/modules/bots/api/bots.api';
import { AccountStep } from '@/modules/bots/components/agent-wizard/account-step';
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
import { formatPercent } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
import { useStrategiesQuery } from '@/modules/strategies/hooks/use-strategies-queries';
import { strategyTypeLabel } from '@/modules/strategies/lib/strategies-labels';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
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

const agentSchema = z.object({
	symbol_id: requiredSelectField('Elige qué quieres operar'),
	strategy_id: requiredSelectField('Elige una estrategia'),
	feature_set_id: requiredSelectField('Elige un conjunto de indicadores'),
	account_id: requiredSelectField('Elige la cuenta'),
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
		description: 'La cuenta define el capital y si opera en paper o en live.',
		fields: ['account_id'],
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
	usePageBreadcrumb([
		{ label: 'Mis agentes', href: '/agents' },
		{ label: 'Nuevo agente' },
	]);
	const navigate = useNavigate();
	const search = routeApi.useSearch();
	const { user } = useAuth();
	const symbolsQuery = useSymbolsQuery({ is_active: true });
	const timeframesQuery = useTimeframesQuery();
	const strategiesQuery = useStrategiesQuery();
	const featureSetsQuery = useFeatureSetsQuery();
	const accountsQuery = useAccountsQuery();
	const createMutation = useCreateBotMutation();
	const transitionMutation = useTransitionBotMutation();
	const [step, setStep] = useState(0);
	// El nombre sugerido solo se aplica hasta que la persona lo edita.
	const [nameTouched, setNameTouched] = useState(false);

	const form = useForm<AgentFormInput, unknown, AgentFormValues>({
		resolver: zodResolver(agentSchema),
		defaultValues: {
			symbol_id: search.symbol_id ? String(search.symbol_id) : null,
			strategy_id: null,
			feature_set_id: null,
			account_id: null,
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
	// Cuentas propias y activas (un admin ve todas en `/accounts`). Los
	// perpetuos solo se operan en paper: con uno elegido, se ocultan las live.
	const perpetual = isPerpetualSymbol(symbol?.symbol);
	const accounts = (accountsQuery.data ?? []).filter(
		(account) =>
			account.user_id === user?.id &&
			account.status === 'active' &&
			!(perpetual && account.mode === 'live'),
	);

	const strategy = strategiesQuery.data?.find(
		(item) => String(item.id) === values.strategy_id,
	);
	const featureSet = featureSetsQuery.data?.find(
		(item) => String(item.id) === values.feature_set_id,
	);
	const account = accounts.find(
		(item) => String(item.id) === values.account_id,
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
		if (!account || !timeframe || riskFraction === null) return;
		createMutation.mutate(
			{
				name: formValues.name,
				symbol_id: Number(formValues.symbol_id),
				strategy_id: Number(formValues.strategy_id),
				feature_set_id: Number(formValues.feature_set_id),
				account_id: account.id,
				timeframe_id: timeframe.id,
				// El modo del agente es siempre el de su cuenta.
				mode: account.mode as BotMode,
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
		{ title: 'Con qué dinero', summary: account?.name },
		{ title: 'Revisar' },
	];
	const current = STEPS[step];
	const fieldError = (name: keyof AgentFormInput) =>
		form.formState.errors[name]?.message;

	return (
		<div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
			<div className="flex flex-col gap-1">
				<h1 className="text-xl font-semibold">Nuevo agente</h1>
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
								name="account_id"
								control={form.control}
								render={({ field }) => (
									<AccountStep
										accounts={accounts}
										isLoading={accountsQuery.isLoading}
										value={field.value}
										onChange={field.onChange}
										currency={symbol?.quote_asset ?? 'USDT'}
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
									<SummaryRow label="Cuenta">
										<span className="inline-flex items-center gap-2">
											{account?.name ?? '—'}
											{account && <BotModeBadge mode={account.mode} />}
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
														accountMode={account?.mode}
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
									{account?.mode === 'live' && (
										<Alert variant="destructive">
											<IconAlertTriangle />
											<AlertTitle>Modo live</AlertTitle>
											<AlertDescription>
												Este agente operará con dinero real.
											</AlertDescription>
										</Alert>
									)}
								</div>
							</div>
						)}

						{/* Errores de los campos que no tienen un input propio */}
						{STEPS[step].fields
							.filter((name) => name !== 'name')
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
							<Button variant="ghost" render={<Link to="/agents" />}>
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
