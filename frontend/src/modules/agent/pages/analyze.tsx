import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2, IconRobot, IconSparkles } from '@tabler/icons-react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import { accountOptions } from '@/modules/accounts/lib/accounts-labels';
import { AnalysisResultPanel } from '@/modules/agent/components/analysis-result-panel';
import { useAnalyzeMutation } from '@/modules/agent/hooks/use-agent-mutations';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import { useFeatureSetsQuery } from '@/modules/features/hooks/use-features-queries';
import { regimeLabel } from '@/modules/features/lib/regime';
import {
	useSymbolsQuery,
	useTimeframesQuery,
} from '@/modules/market/hooks/use-market-queries';
import {
	symbolOptions,
	timeframeOptions,
} from '@/modules/market/lib/market-labels';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
import { useStrategiesQuery } from '@/modules/strategies/hooks/use-strategies-queries';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardContent,
	CardDescription,
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
import { Skeleton } from '@/modules/ui/components/skeleton';

const analyzeSchema = z.object({
	symbol_id: requiredSelectField('Elige el símbolo'),
	timeframe_id: requiredSelectField('Elige el timeframe'),
	strategy_id: requiredSelectField('Elige la estrategia'),
	account_id: requiredSelectField('Elige la cuenta'),
	feature_set_id: requiredSelectField('Elige el set de indicadores'),
});

type AnalyzeFormInput = z.input<typeof analyzeSchema>;
type AnalyzeFormOutput = z.output<typeof analyzeSchema>;

type SelectFieldName = keyof AnalyzeFormInput;

function AnalyzingState() {
	return (
		<Card>
			<CardContent className="flex flex-col items-center gap-3 py-12 text-center">
				<IconLoader2 className="size-8 animate-spin text-muted-foreground" />
				<p className="font-medium">Analizando…</p>
				<p className="max-w-sm text-sm text-muted-foreground">
					El agente revisa el régimen, las reglas y el riesgo/beneficio. Puede
					tardar hasta un minuto; no cierres esta página.
				</p>
				<div className="mt-4 grid w-full max-w-md gap-3">
					<Skeleton className="h-10 w-full" />
					<Skeleton className="h-24 w-full" />
				</div>
			</CardContent>
		</Card>
	);
}

function EmptyState() {
	return (
		<div className="flex flex-col items-center gap-3 rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
			<IconRobot className="size-8" />
			<p>Elige los parámetros y ejecuta el análisis.</p>
			<p className="max-w-sm">
				El agente de IA solo propone la operación si pasa el filtro de régimen,
				las reglas de la estrategia y un riesgo/beneficio mínimo de 2:1.
			</p>
		</div>
	);
}

export function AgentAnalyzePage() {
	usePageBreadcrumb([{ label: 'Trading' }, { label: 'Agente de IA' }]);
	const { user } = useAuth();
	const symbolsQuery = useSymbolsQuery({ is_active: true });
	const timeframesQuery = useTimeframesQuery();
	const strategiesQuery = useStrategiesQuery();
	const accountsQuery = useAccountsQuery();
	const featureSetsQuery = useFeatureSetsQuery();
	const analyzeMutation = useAnalyzeMutation();

	const form = useForm<AnalyzeFormInput, unknown, AnalyzeFormOutput>({
		resolver: zodResolver(analyzeSchema),
		defaultValues: {
			symbol_id: null,
			timeframe_id: null,
			strategy_id: null,
			account_id: null,
			feature_set_id: null,
		},
	});

	const strategyId = useWatch({ control: form.control, name: 'strategy_id' });
	const selectedStrategy = strategiesQuery.data?.find(
		(strategy) => String(strategy.id) === strategyId,
	);
	const requiredRegime = selectedStrategy?.parameters.regime_required;

	// Solo cuentas propias y activas: un admin recibe todas las del sistema.
	const ownAccounts = accountsQuery.data?.filter(
		(account) =>
			account.status === 'active' && (!user || account.user_id === user.id),
	);

	const fields: {
		name: SelectFieldName;
		label: string;
		options: { value: string; label: string }[];
		description?: string;
	}[] = [
		{
			name: 'symbol_id',
			label: 'Símbolo',
			options: symbolOptions(symbolsQuery.data),
		},
		{
			name: 'timeframe_id',
			label: 'Timeframe',
			options: timeframeOptions(timeframesQuery.data),
		},
		{
			name: 'strategy_id',
			label: 'Estrategia',
			options: (strategiesQuery.data ?? []).map((strategy) => ({
				value: String(strategy.id),
				label: `${strategy.name} v${strategy.version}`,
			})),
			description: selectedStrategy
				? requiredRegime
					? `Requiere régimen: ${regimeLabel(requiredRegime)}.`
					: 'Opera en cualquier régimen.'
				: undefined,
		},
		{
			name: 'account_id',
			label: 'Cuenta',
			options: accountOptions(ownAccounts),
			description:
				'El capital es el saldo libre en la moneda base de la cuenta.',
		},
		{
			name: 'feature_set_id',
			label: 'Set de indicadores',
			options: (featureSetsQuery.data ?? []).map((featureSet) => ({
				value: String(featureSet.id),
				label: `${featureSet.name} v${featureSet.version}`,
			})),
		},
	];

	function handleSubmit(values: AnalyzeFormOutput) {
		analyzeMutation.mutate({
			symbol_id: Number(values.symbol_id),
			timeframe_id: Number(values.timeframe_id),
			strategy_id: Number(values.strategy_id),
			account_id: Number(values.account_id),
			feature_set_id: Number(values.feature_set_id),
		});
	}

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Agente de IA"
				description="Evalúa una operación contra tu estrategia: régimen, reglas, agente de IA y riesgo/beneficio."
			/>
			<div className="grid items-start gap-6 lg:grid-cols-[22rem_1fr]">
				<Card>
					<CardHeader>
						<CardTitle>Parámetros</CardTitle>
						<CardDescription>
							Usa la última vela guardada y sus indicadores calculados.
						</CardDescription>
					</CardHeader>
					<CardContent>
						<form onSubmit={form.handleSubmit(handleSubmit)} noValidate>
							<FieldGroup className="gap-5">
								{fields.map((item) => (
									<Controller
										key={item.name}
										name={item.name}
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor={`agent-${item.name}`} required>
													{item.label}
												</FieldLabel>
												<OptionSelect
													id={`agent-${item.name}`}
													value={field.value}
													onChange={field.onChange}
													options={item.options}
													aria-invalid={fieldState.invalid}
												/>
												{item.description && (
													<FieldDescription>
														{item.description}
													</FieldDescription>
												)}
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
								))}
								<Button
									type="submit"
									className="w-full"
									disabled={analyzeMutation.isPending}
								>
									{analyzeMutation.isPending ? (
										<IconLoader2 className="animate-spin" />
									) : (
										<IconSparkles />
									)}
									{analyzeMutation.isPending
										? 'Analizando…'
										: 'Ejecutar análisis'}
								</Button>
							</FieldGroup>
						</form>
					</CardContent>
				</Card>

				<div className="min-w-0">
					{analyzeMutation.isPending ? (
						<AnalyzingState />
					) : analyzeMutation.isError ? (
						<ErrorAlert
							title="No pudimos completar el análisis"
							error={analyzeMutation.error}
						/>
					) : analyzeMutation.data ? (
						<AnalysisResultPanel result={analyzeMutation.data} />
					) : (
						<EmptyState />
					)}
				</div>
			</div>
		</div>
	);
}
