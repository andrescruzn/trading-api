import { getRouteApi } from '@tanstack/react-router';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { Candle } from '@/modules/market/api/market.api';
import {
	useCandlesQuery,
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

const routeApi = getRouteApi('/_app/market/candles');

const columns: DataTableColumn<Candle>[] = [
	{
		id: 'ts',
		header: 'Fecha',
		cell: (row) => formatDateTime(row.ts),
		skeletonClassName: 'w-32',
	},
	...(['open', 'high', 'low', 'close'] as const).map(
		(key): DataTableColumn<Candle> => ({
			id: key,
			header: { open: 'Apertura', high: 'Máximo', low: 'Mínimo', close: 'Cierre' }[
				key
			],
			className: 'text-right font-mono tabular-nums',
			cell: (row) => formatNumber(row[key]),
		}),
	),
	{
		id: 'volume',
		header: 'Volumen',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatNumber(row.volume, 4),
	},
];

export function CandlesPage() {
	usePageBreadcrumb([{ label: 'Mercado' }, { label: 'Velas OHLCV' }]);
	const search = routeApi.useSearch();
	const navigate = routeApi.useNavigate();
	const [limit, setLimit] = useState('100');

	const symbolsQuery = useSymbolsQuery({ is_active: true });
	const timeframesQuery = useTimeframesQuery();

	// El símbolo y el timeframe viven en la URL (`?symbol_id=`): así "Ver velas"
	// desde Símbolos llega preseleccionado y el enlace se puede compartir.
	const symbolId = search.symbol_id;
	const timeframeId = search.timeframe_id ?? timeframesQuery.data?.[0]?.id;

	const candlesQuery = useCandlesQuery({
		symbol_id: symbolId,
		timeframe_id: timeframeId,
		limit: Number(limit),
	});

	function updateSearch(next: { symbol_id?: number; timeframe_id?: number }) {
		navigate({ search: (prev) => ({ ...prev, ...next }), replace: true });
	}

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Velas OHLCV"
				description="Precios de apertura, máximo, mínimo y cierre guardados para cada símbolo."
			/>
			<div className="grid gap-3 sm:grid-cols-3 lg:max-w-3xl">
				<Field>
					<FieldLabel htmlFor="candles-symbol">Símbolo</FieldLabel>
					<OptionSelect
						id="candles-symbol"
						size="sm"
						value={symbolId ? String(symbolId) : null}
						onChange={(value) =>
							updateSearch({ symbol_id: value ? Number(value) : undefined })
						}
						options={symbolOptions(symbolsQuery.data)}
						placeholder="Elige un símbolo"
					/>
				</Field>
				<Field>
					<FieldLabel htmlFor="candles-timeframe">Timeframe</FieldLabel>
					<OptionSelect
						id="candles-timeframe"
						size="sm"
						value={timeframeId ? String(timeframeId) : null}
						onChange={(value) =>
							updateSearch({ timeframe_id: value ? Number(value) : undefined })
						}
						options={timeframeOptions(timeframesQuery.data)}
					/>
				</Field>
				<Field>
					<FieldLabel htmlFor="candles-limit">Cantidad</FieldLabel>
					<OptionSelect
						id="candles-limit"
						size="sm"
						value={limit}
						onChange={(value) => setLimit(value ?? '100')}
						options={CANDLE_LIMIT_OPTIONS}
					/>
				</Field>
			</div>
			{symbolId ? (
				<DataTable
					columns={columns}
					rows={candlesQuery.data}
					getRowId={(row) => row.id}
					isLoading={candlesQuery.isLoading}
					error={candlesQuery.error}
					errorTitle="No pudimos cargar las velas"
					empty="No hay velas guardadas para este símbolo y timeframe. Un administrador puede descargarlas desde Descargar velas."
				/>
			) : (
				<p className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
					Elige un símbolo para ver sus velas.
				</p>
			)}
		</div>
	);
}
