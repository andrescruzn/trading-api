import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { CandleFeature } from '@/modules/features/api/features.api';
import { RegimeBadge } from '@/modules/features/components/regime-badge';
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
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDateTime, formatNumber } from '@/modules/shared/lib/format';
import { Field, FieldLabel } from '@/modules/ui/components/field';

type NumericFeatureKey =
	| 'rsi_14'
	| 'ema_20'
	| 'ema_50'
	| 'ema_200'
	| 'macd'
	| 'macd_signal'
	| 'atr_14'
	| 'bb_upper'
	| 'bb_lower'
	| 'vol_rel';

// RSI y volumen relativo son índices pequeños: con 2 decimales basta. El resto
// está en unidades de precio y usa los decimales según la magnitud.
const NUMERIC_COLUMNS: {
	key: NumericFeatureKey;
	header: string;
	digits?: number;
}[] = [
	{ key: 'rsi_14', header: 'RSI 14', digits: 2 },
	{ key: 'ema_20', header: 'EMA 20' },
	{ key: 'ema_50', header: 'EMA 50' },
	{ key: 'ema_200', header: 'EMA 200' },
	{ key: 'macd', header: 'MACD' },
	{ key: 'macd_signal', header: 'Señal MACD' },
	{ key: 'atr_14', header: 'ATR 14' },
	{ key: 'bb_upper', header: 'BB superior' },
	{ key: 'bb_lower', header: 'BB inferior' },
	{ key: 'vol_rel', header: 'Vol. relativo', digits: 2 },
];

const columns: DataTableColumn<CandleFeature>[] = [
	{
		id: 'ts',
		header: 'Fecha',
		className: 'whitespace-nowrap',
		cell: (row) => formatDateTime(row.ts),
		skeletonClassName: 'w-32',
	},
	{
		id: 'regime',
		header: 'Régimen',
		cell: (row) => <RegimeBadge regime={row.features?.regime} />,
		skeletonClassName: 'w-24',
	},
	...NUMERIC_COLUMNS.map(
		(column): DataTableColumn<CandleFeature> => ({
			id: column.key,
			header: column.header,
			className: 'text-right font-mono tabular-nums',
			cell: (row) => formatNumber(row.features?.[column.key], column.digits),
		}),
	),
];

export function IndicatorsPage() {
	usePageBreadcrumb([{ label: 'Mercado' }, { label: 'Indicadores' }]);
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
				description="RSI, EMA, MACD, ATR, bandas de Bollinger y régimen de mercado calculados por vela."
			/>
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
					<FieldLabel htmlFor="indicators-feature-set">Feature set</FieldLabel>
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
					<DataTable
						columns={columns}
						rows={featuresQuery.data}
						getRowId={(row) => row.id}
						isLoading={featuresQuery.isLoading}
						error={featuresQuery.error}
						errorTitle="No pudimos cargar los indicadores"
						empty="No hay indicadores calculados para este símbolo y timeframe. Un administrador puede calcularlos desde Feature sets."
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
