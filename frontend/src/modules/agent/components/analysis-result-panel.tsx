import {
	IconCircleCheck,
	IconCircleDashed,
	IconCircleX,
} from '@tabler/icons-react';
import type { AnalysisResult } from '@/modules/agent/api/agent.api';
import {
	type AnalysisPhase,
	analysisPhases,
	formatRiskReward,
	formatRuleValue,
	MIN_RR_RATIO,
	PHASE_STATUS_LABELS,
	rejectionReasonLabel,
	ruleOperatorSymbol,
} from '@/modules/agent/lib/agent-labels';
import {
	REGIME_BADGE_VARIANT,
	type Regime,
	regimeLabel,
} from '@/modules/features/lib/regime';
import { StatCard } from '@/modules/shared/components/stat-card';
import {
	formatNumber,
	formatPercent,
	formatPrice,
} from '@/modules/shared/lib/format';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Badge } from '@/modules/ui/components/badge';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from '@/modules/ui/components/table';

const USD_QUOTES = ['USD', 'USDT', 'USDC'];

function PhaseBadge({ phase }: { phase: AnalysisPhase }) {
	const statusText = `${phase.label}: ${PHASE_STATUS_LABELS[phase.status]}`;

	if (phase.status === 'pass') {
		return (
			<Badge
				variant="outline"
				className="h-7 border-chart-1/40 px-2.5 text-sm text-chart-1"
				title={statusText}
			>
				<IconCircleCheck aria-hidden="true" />
				{phase.label}
				<span className="sr-only">: {PHASE_STATUS_LABELS[phase.status]}</span>
			</Badge>
		);
	}
	if (phase.status === 'fail') {
		return (
			<Badge variant="destructive" className="h-7 px-2.5 text-sm" title={statusText}>
				<IconCircleX aria-hidden="true" />
				{phase.label}
				<span className="sr-only">: {PHASE_STATUS_LABELS[phase.status]}</span>
			</Badge>
		);
	}
	return (
		<Badge
			variant="outline"
			className="h-7 px-2.5 text-sm text-muted-foreground"
			title={statusText}
		>
			<IconCircleDashed aria-hidden="true" />
			{phase.label}
			<span className="sr-only">: {PHASE_STATUS_LABELS[phase.status]}</span>
		</Badge>
	);
}

function SectionTitle({ children }: { children: string }) {
	return <h2 className="text-sm font-medium text-muted-foreground">{children}</h2>;
}

export function AnalysisResultPanel({ result }: { result: AnalysisResult }) {
	const approved = result.decision === 'APPROVED';
	const { meta } = result;
	const phases = analysisPhases(result);
	const hasLevels =
		result.entry !== null || result.stop_loss !== null || result.take_profit !== null;
	// `BTC/USDT` → `BTC` / `USDT`: el tamaño de posición está en unidades del
	// activo base y el `$` solo aplica si la cotización es en dólares.
	const [baseAsset = '', quoteAsset = ''] = meta.symbol?.split('/') ?? [];
	const isUsdQuote = USD_QUOTES.includes(quoteAsset.toUpperCase());
	const price = (value: number | null | undefined) =>
		isUsdQuote ? formatPrice(value) : formatNumber(value);
	const regime = meta.regime as Regime | undefined;

	return (
		<div className="flex flex-col gap-6">
			{approved ? (
				<Alert className="border-chart-1/40 text-chart-1">
					<IconCircleCheck />
					<AlertTitle>Operación aprobada</AlertTitle>
					<AlertDescription>
						Pasó el filtro de régimen, las reglas de la estrategia, el agente de
						IA y el riesgo/beneficio mínimo de {MIN_RR_RATIO}:1.
					</AlertDescription>
				</Alert>
			) : (
				<Alert variant="destructive">
					<IconCircleX />
					<AlertTitle>Operación rechazada</AlertTitle>
					<AlertDescription>{rejectionReasonLabel(result)}</AlertDescription>
				</Alert>
			)}

			{meta.symbol && (
				<div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm text-muted-foreground">
					<span className="font-mono font-medium text-foreground">{meta.symbol}</span>
					{meta.timeframe && <span className="font-mono">{meta.timeframe}</span>}
					{meta.strategy && (
						<span>
							{meta.strategy}
							{meta.strategy_version ? ` v${meta.strategy_version}` : ''}
						</span>
					)}
					{meta.current_price !== undefined && (
						<span>
							Precio actual:{' '}
							<span className="font-mono tabular-nums text-foreground">
								{price(meta.current_price)}
							</span>
						</span>
					)}
					{regime && (
						<Badge variant={REGIME_BADGE_VARIANT[regime] ?? 'outline'}>
							{regimeLabel(regime)}
						</Badge>
					)}
				</div>
			)}

			<section className="flex flex-col gap-3">
				<SectionTitle>Fases del análisis</SectionTitle>
				<div className="flex flex-wrap gap-2">
					{phases.map((phase) => (
						<PhaseBadge key={phase.id} phase={phase} />
					))}
				</div>
			</section>

			<section className="flex flex-col gap-3">
				<SectionTitle>Niveles</SectionTitle>
				{hasLevels ? (
					<div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
						<StatCard label="Entrada" value={price(result.entry)} />
						<StatCard
							label="Stop loss"
							value={
								<span className="text-destructive">{price(result.stop_loss)}</span>
							}
						/>
						<StatCard
							label="Take profit"
							value={<span className="text-chart-1">{price(result.take_profit)}</span>}
						/>
						<StatCard
							label="Tamaño de posición"
							value={
								result.position_size === null
									? '—'
									: `${formatNumber(result.position_size, 8)} ${baseAsset}`.trim()
							}
							hint={
								meta.capital !== undefined
									? `Capital: ${formatNumber(meta.capital, 2)} ${meta.base_currency ?? ''}`.trim()
									: undefined
							}
						/>
						<StatCard
							label="Riesgo/beneficio"
							value={
								<span
									className={
										result.rr_ratio === null
											? undefined
											: result.rr_check_passed
												? 'text-chart-1'
												: 'text-destructive'
									}
								>
									{formatRiskReward(result.rr_ratio)}
								</span>
							}
							hint={`Mínimo ${MIN_RR_RATIO}:1`}
						/>
						<StatCard
							label="Confianza del agente"
							value={formatPercent(result.confidence, 0)}
						/>
					</div>
				) : (
					<p className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">
						El análisis se detuvo antes de calcular entrada, stop loss y take
						profit.
					</p>
				)}
			</section>

			<Card>
				<CardHeader>
					<CardTitle>Razonamiento</CardTitle>
					<CardDescription>
						Por qué se tomó la decisión, según la fase que la definió.
					</CardDescription>
				</CardHeader>
				<CardContent>
					<p className="text-sm leading-relaxed whitespace-pre-wrap">
						{result.reasoning || 'El agente no dio una explicación.'}
					</p>
				</CardContent>
			</Card>

			{result.rules_detail.length > 0 && (
				<section className="flex flex-col gap-3">
					<SectionTitle>Reglas de la estrategia</SectionTitle>
					<Table>
						<TableHeader>
							<TableRow>
								<TableHead>Regla</TableHead>
								<TableHead className="text-right">Valor actual</TableHead>
								<TableHead className="text-right">Resultado</TableHead>
							</TableRow>
						</TableHeader>
						<TableBody>
							{result.rules_detail.map((rule, index) => (
								<TableRow key={`${rule.indicator}-${index}`}>
									<TableCell className="font-mono">
										{rule.indicator}{' '}
										<span className="text-muted-foreground">
											{ruleOperatorSymbol(rule.operator)}
										</span>{' '}
										{formatRuleValue(rule.threshold)}
									</TableCell>
									<TableCell className="text-right font-mono tabular-nums">
										{formatRuleValue(rule.actual_value)}
									</TableCell>
									<TableCell className="text-right">
										{rule.passed ? (
											<Badge
												variant="outline"
												className="border-chart-1/40 text-chart-1"
											>
												<IconCircleCheck aria-hidden="true" />
												Cumple
											</Badge>
										) : (
											<Badge variant="destructive">
												<IconCircleX aria-hidden="true" />
												No cumple
											</Badge>
										)}
									</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</section>
			)}
		</div>
	);
}
