import {
	IconAlertTriangle,
	IconRobot,
	IconSparkles,
} from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import type { AssetClass } from '@/modules/market/api/market.api';
import type { RecommendationItem } from '@/modules/market/api/recommendations.api';
import { useGenerateRecommendationsMutation } from '@/modules/market/hooks/use-recommendation-mutations';
import { useLatestRecommendationQuery } from '@/modules/market/hooks/use-recommendation-queries';
import { ASSET_CLASS_LABELS } from '@/modules/market/lib/market-labels';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { formatDateTime, formatPercent } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardAction,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { Skeleton } from '@/modules/ui/components/skeleton';
import { toast } from '@/modules/ui/components/toast';

function RecommendationCard({
	item,
	canCreate,
}: {
	item: RecommendationItem;
	canCreate: boolean;
}) {
	return (
		<li className="flex flex-col gap-3 rounded-lg border p-4">
			<div className="flex flex-wrap items-start justify-between gap-2">
				<div className="flex flex-col gap-1">
					<span className="font-mono font-medium">{item.symbol}</span>
					<span className="text-xs text-muted-foreground">
						{item.strategy_name} v{item.strategy_version}
						{item.timeframe ? ` · ${item.timeframe}` : ''}
					</span>
				</div>
				{item.confidence !== null && (
					<Badge variant="secondary" className="tabular-nums">
						Confianza {formatPercent(item.confidence, 0)}
					</Badge>
				)}
			</div>
			<p className="text-sm">{item.reasoning}</p>
			{item.risks && (
				<p className="flex gap-1.5 text-sm text-muted-foreground">
					<IconAlertTriangle className="mt-0.5 size-4 shrink-0" />
					<span>{item.risks}</span>
				</p>
			)}
			{canCreate && (
				<Button
					variant="outline"
					size="sm"
					className="mt-auto self-start"
					render={
						<Link
							to="/agents/new"
							search={{
								symbol_id: item.symbol_id,
								strategy_id: item.strategy_id,
							}}
						/>
					}
				>
					<IconRobot />
					Crear agente
				</Button>
			)}
		</li>
	);
}

/**
 * Recomendaciones de la IA sobre en qué mercados crear un agente. Todos ven
 * la última; solo el super admin pide nuevas (cada pedido llama al LLM).
 */
export function AiRecommendationsPanel({
	assetClass,
	canManage,
}: {
	/** Filtro de clase activo en el explorador: se usa al pedir nuevas. */
	assetClass?: AssetClass;
	canManage: boolean;
}) {
	const latestQuery = useLatestRecommendationQuery();
	const generateMutation = useGenerateRecommendationsMutation();
	const recommendation = latestQuery.data;
	const isGenerating = generateMutation.isPending;

	function handleGenerate() {
		generateMutation.mutate(
			{ asset_class: assetClass },
			{
				onSuccess: () =>
					toast.add({ title: 'Recomendaciones listas', type: 'success' }),
				onError: (error) =>
					toast.add({
						title: 'No pudimos generar recomendaciones',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	const scope = recommendation?.asset_class
		? ASSET_CLASS_LABELS[recommendation.asset_class]
		: 'Todas las clases';

	return (
		<Card>
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<IconSparkles className="size-4" />
					Recomendaciones de la IA
				</CardTitle>
				<CardDescription>
					{recommendation
						? `${formatDateTime(recommendation.created_at)} · ${scope}`
						: 'La IA revisa el ranking y sugiere en qué mercados crear un agente y con qué estrategia.'}
				</CardDescription>
				{canManage && (
					<CardAction>
						<Button size="sm" onClick={handleGenerate} disabled={isGenerating}>
							<IconSparkles />
							{isGenerating ? 'Analizando…' : 'Pedir recomendaciones'}
						</Button>
					</CardAction>
				)}
			</CardHeader>

			<CardContent className="flex flex-col gap-4">
				{isGenerating && (
					<p className="text-sm text-muted-foreground">
						La IA está revisando los mercados. Puede tardar hasta un minuto.
					</p>
				)}

				{latestQuery.isLoading ? (
					<div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
						<Skeleton className="h-40" />
						<Skeleton className="h-40" />
						<Skeleton className="h-40" />
					</div>
				) : latestQuery.error ? (
					<ErrorAlert
						title="No pudimos cargar las recomendaciones"
						error={latestQuery.error}
					/>
				) : !recommendation ? (
					!isGenerating && (
						<p className="text-sm text-muted-foreground">
							{canManage
								? 'Aún no hay recomendaciones. Pulsa «Pedir recomendaciones» para que la IA revise el ranking.'
								: 'Aún no hay recomendaciones. Un administrador puede pedirlas.'}
						</p>
					)
				) : (
					<>
						{recommendation.summary && (
							<p className="text-sm">{recommendation.summary}</p>
						)}
						<ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
							{recommendation.items.map((item) => (
								<RecommendationCard
									key={item.symbol_id}
									item={item}
									canCreate={canManage}
								/>
							))}
						</ul>
					</>
				)}
			</CardContent>

			<CardFooter>
				<p className="text-xs text-muted-foreground">
					Son sugerencias, no garantías. Cada operación del agente pasa igual
					por el filtro de régimen, la regla del 1 % y el riesgo/beneficio
					mínimo de 2:1.
				</p>
			</CardFooter>
		</Card>
	);
}
