import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { CandleFeaturesTable } from '@/modules/features/components/candle-features-table';
import { IndicatorsGlossary } from '@/modules/features/components/indicators-glossary';
import {
	useCandleFeaturesQuery,
	useFeatureSetsQuery,
} from '@/modules/features/hooks/use-features-queries';
import { featureSetOptions } from '@/modules/features/lib/features-labels';
import {
	useSymbolsQuery,
	useTimeframesQuery,
} from '@/modules/market/hooks/use-market-queries';
import {
	CANDLE_LIMIT_OPTIONS,
	symbolOptions,
	timeframeOptions,
} from '@/modules/market/lib/market-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { Field, FieldLabel } from '@/modules/ui/components/field';

// Visor de cualquier símbolo, timeframe y conjunto para revisar el cálculo. El
// usuario ve los indicadores de su agente en la pestaña Mercado del agente.
export function AdminIndicatorsPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Indicadores' }]);
	const [symbolId, setSymbolId] = useState<string | null>(null);
	const [timeframeChoice, setTimeframeChoice] = useState<string | null>(null);
	const [featureSetChoice, setFeatureSetChoice] = useState<string | null>(null);
	const [limit, setLimit] = useState('100');

	const symbolsQuery = useSymbolsQuery({ is_active: true });
	const timeframesQuery = useTimeframesQuery();
	const featureSetsQuery = useFeatureSetsQuery();

	// Timeframe y feature set arrancan con el primero del catálogo para que
	// basten un clic (el símbolo) para ver datos.
	const firstTimeframeId = timeframesQuery.data?.[0]?.id;
	const firstFeatureSetId = featureSetsQuery.data?.[0]?.id;
	const timeframeId =
		timeframeChoice ?? (firstTimeframeId ? String(firstTimeframeId) : null);
	const featureSetId =
		featureSetChoice ?? (firstFeatureSetId ? String(firstFeatureSetId) : null);

	const featuresQuery = useCandleFeaturesQuery({
		symbol_id: symbolId ? Number(symbolId) : undefined,
		timeframe_id: timeframeId ? Number(timeframeId) : undefined,
		feature_set_id: featureSetId ? Number(featureSetId) : undefined,
		limit: Number(limit),
	});

	const rowCount = featuresQuery.data?.length ?? 0;

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Indicadores"
				description="Indicadores calculados por vela para cualquier símbolo, timeframe y conjunto."
			/>
			<IndicatorsGlossary />
			<div className="grid gap-3 sm:grid-cols-2 lg:max-w-4xl lg:grid-cols-4">
				<Field>
					<FieldLabel htmlFor="indicators-symbol">Símbolo</FieldLabel>
					<OptionSelect
						id="indicators-symbol"
						size="sm"
						value={symbolId}
						onChange={setSymbolId}
						options={symbolOptions(symbolsQuery.data)}
						placeholder="Elige un símbolo"
					/>
				</Field>
				<Field>
					<FieldLabel htmlFor="indicators-timeframe">Timeframe</FieldLabel>
					<OptionSelect
						id="indicators-timeframe"
						size="sm"
						value={timeframeId}
						onChange={setTimeframeChoice}
						options={timeframeOptions(timeframesQuery.data)}
					/>
				</Field>
				<Field>
					<FieldLabel htmlFor="indicators-feature-set">Conjunto</FieldLabel>
					<OptionSelect
						id="indicators-feature-set"
						size="sm"
						value={featureSetId}
						onChange={setFeatureSetChoice}
						options={featureSetOptions(featureSetsQuery.data)}
					/>
				</Field>
				<Field>
					<FieldLabel htmlFor="indicators-limit">Cantidad</FieldLabel>
					<OptionSelect
						id="indicators-limit"
						size="sm"
						value={limit}
						onChange={(value) => setLimit(value ?? '100')}
						options={CANDLE_LIMIT_OPTIONS}
					/>
				</Field>
			</div>
			{symbolId ? (
				<div className="flex flex-col gap-2">
					{!featuresQuery.isLoading && rowCount > 0 && (
						<p className="text-sm text-muted-foreground">
							{rowCount.toLocaleString('es-CO')} velas, de la más reciente a la
							más antigua.
						</p>
					)}
					<CandleFeaturesTable
						rows={featuresQuery.data}
						isLoading={featuresQuery.isLoading}
						error={featuresQuery.error}
						empty="No hay indicadores calculados para este símbolo, timeframe y conjunto. Se calculan solos para los agentes activos, o a mano desde Conjuntos de indicadores."
					/>
				</div>
			) : (
				<p className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
					Elige un símbolo para ver sus indicadores.
				</p>
			)}
		</div>
	);
}
