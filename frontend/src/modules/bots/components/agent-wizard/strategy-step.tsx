import { IconInfoCircle } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { ChoiceCard } from '@/modules/bots/components/agent-wizard/choice-card';
import {
	isFeatureSetCompatible,
	recommendedFeatureSet,
} from '@/modules/bots/lib/agent-wizard';
import type { FeatureSet } from '@/modules/features/api/features.api';
import { INDICATOR_GROUP_LABELS } from '@/modules/features/lib/features-labels';
import { regimeLabel } from '@/modules/features/lib/regime';
import type { Strategy } from '@/modules/strategies/api/strategies.api';
import { strategyTypeLabel } from '@/modules/strategies/lib/strategies-labels';
import { Badge } from '@/modules/ui/components/badge';
import { Skeleton } from '@/modules/ui/components/skeleton';

type StrategyStepProps = {
	strategies: Strategy[] | undefined;
	featureSets: FeatureSet[] | undefined;
	isLoading: boolean;
	strategyId: string | null;
	featureSetId: string | null;
	onStrategyChange: (
		strategy: Strategy,
		recommended: FeatureSet | null,
	) => void;
	onFeatureSetChange: (value: string) => void;
};

/**
 * Paso 2: cómo opera el agente. La estrategia define las reglas, el
 * timeframe y el riesgo; el conjunto de indicadores, qué datos revisa la IA.
 * Solo se ofrecen conjuntos que calculan todo lo que piden las reglas.
 */
export function StrategyStep({
	strategies,
	featureSets,
	isLoading,
	strategyId,
	featureSetId,
	onStrategyChange,
	onFeatureSetChange,
}: StrategyStepProps) {
	const strategy = strategies?.find((item) => String(item.id) === strategyId);
	const compatible = strategy
		? (featureSets ?? []).filter((featureSet) =>
				isFeatureSetCompatible(strategy, featureSet),
			)
		: [];
	const recommended = strategy
		? recommendedFeatureSet(strategy, compatible)
		: null;

	if (isLoading) {
		return (
			<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
				{Array.from({ length: 6 }, (_, index) => (
					<Skeleton key={index} className="h-36 rounded-xl" />
				))}
			</div>
		);
	}

	if (!strategies?.length) {
		return (
			<p className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">
				Aún no hay estrategias. Un administrador debe crear al menos una.
			</p>
		);
	}

	return (
		<div className="flex flex-col gap-8">
			<section className="flex flex-col gap-3">
				<h3 className="text-sm font-medium">Estrategia</h3>
				<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
					{strategies.map((item) => {
						const params = item.parameters;
						return (
							<ChoiceCard
								key={item.id}
								selected={strategyId === String(item.id)}
								onSelect={() => {
									const itemCompatible = (featureSets ?? []).filter(
										(featureSet) => isFeatureSetCompatible(item, featureSet),
									);
									onStrategyChange(
										item,
										recommendedFeatureSet(item, itemCompatible),
									);
								}}
								eyebrow={strategyTypeLabel(params.strategy_type)}
								title={`${item.name} v${item.version}`}
								description={item.description}
								footer={
									<span className="flex flex-wrap gap-1.5">
										<Badge variant="outline" className="font-mono">
											{params.timeframe_code ?? '—'}
										</Badge>
										<Badge variant="secondary">
											{params.regime_required
												? regimeLabel(params.regime_required)
												: 'Cualquier régimen'}
										</Badge>
									</span>
								}
							/>
						);
					})}
				</div>
				<p className="text-sm text-muted-foreground">
					¿Quieres ver las reglas de cada una?{' '}
					<Link to="/strategies" className="text-primary hover:underline">
						Abre Estrategias
					</Link>
					.
				</p>
			</section>

			{strategy && (
				<section className="flex animate-in flex-col gap-3 fade-in slide-in-from-bottom-2">
					<div className="flex flex-col gap-1">
						<h3 className="text-sm font-medium">
							Indicadores que revisa la IA
						</h3>
						<p className="flex items-start gap-2 text-sm text-muted-foreground">
							<IconInfoCircle className="mt-0.5 size-4 shrink-0" />
							Los indicadores son cálculos sobre las velas (tendencia, fuerza,
							volatilidad). La estrategia los usa en sus reglas y la IA los lee
							para decidir. Te mostramos solo los conjuntos que sirven para esta
							estrategia.
						</p>
					</div>
					{compatible.length === 0 ? (
						<p className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">
							Ningún conjunto de indicadores calcula todo lo que pide esta
							estrategia. Un administrador debe crear uno compatible.
						</p>
					) : (
						<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
							{compatible.map((featureSet) => (
								<ChoiceCard
									key={featureSet.id}
									selected={featureSetId === String(featureSet.id)}
									onSelect={() => onFeatureSetChange(String(featureSet.id))}
									eyebrow={
										recommended?.id === featureSet.id ? (
											<span className="font-medium text-primary">
												Recomendado
											</span>
										) : undefined
									}
									title={featureSet.name}
									description={featureSet.description}
									footer={
										<span className="flex flex-wrap gap-1.5">
											{featureSet.indicators.map((group) => (
												<Badge key={group} variant="outline">
													{INDICATOR_GROUP_LABELS[group] ?? group}
												</Badge>
											))}
										</span>
									}
								/>
							))}
						</div>
					)}
				</section>
			)}
		</div>
	);
}
