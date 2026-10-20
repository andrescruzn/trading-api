import { getRouteApi } from '@tanstack/react-router';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { CandlesTable } from '@/modules/market/components/candles-table';
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
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { Field, FieldLabel } from '@/modules/ui/components/field';

const routeApi = getRouteApi('/_app/admin/candles/view');

// Visor de cualquier símbolo y timeframe para revisar la ingesta. El usuario
// ve las velas de su agente en la pestaña Mercado del agente.
export function AdminCandlesPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Velas' }]);
	const search = routeApi.useSearch();
	const navigate = routeApi.useNavigate();
	const [limit, setLimit] = useState('100');

	const symbolsQuery = useSymbolsQuery({ is_active: true });
	const timeframesQuery = useTimeframesQuery();

	// El símbolo y el timeframe viven en la URL (`?symbol_id=`): así "Ver velas"
	// desde Descargar velas llega preseleccionado y el enlace se puede compartir.
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
				description="Precios de apertura, máximo, mínimo y cierre guardados para cada símbolo y timeframe."
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
				<CandlesTable
					rows={candlesQuery.data}
					isLoading={candlesQuery.isLoading}
					error={candlesQuery.error}
					empty="No hay velas guardadas para este símbolo y timeframe. Descárgalas desde Descargar velas."
				/>
			) : (
				<p className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
					Elige un símbolo para ver sus velas.
				</p>
			)}
		</div>
	);
}
