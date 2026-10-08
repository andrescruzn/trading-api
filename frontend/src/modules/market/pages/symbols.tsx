import { IconChartCandle } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { AssetClass, MarketSymbol } from '@/modules/market/api/market.api';
import {
	useExchangesQuery,
	useSymbolsQuery,
} from '@/modules/market/hooks/use-market-queries';
import {
	ASSET_CLASS_LABELS,
	ASSET_CLASS_OPTIONS,
} from '@/modules/market/lib/market-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';

const ALL = 'all';

const columns: DataTableColumn<MarketSymbol>[] = [
	{
		id: 'symbol',
		header: 'Símbolo',
		cell: (row) => <span className="font-mono font-medium">{row.symbol}</span>,
	},
	{ id: 'exchange', header: 'Exchange', cell: (row) => row.exchange_name ?? '—' },
	{ id: 'base', header: 'Base', cell: (row) => row.base_asset ?? '—' },
	{ id: 'quote', header: 'Cotización', cell: (row) => row.quote_asset ?? '—' },
	{
		id: 'class',
		header: 'Clase',
		cell: (row) => (
			<Badge variant="secondary">{ASSET_CLASS_LABELS[row.asset_class]}</Badge>
		),
	},
	{
		id: 'actions',
		header: <span className="sr-only">Acciones</span>,
		className: 'text-right',
		cell: (row) => (
			<Button
				variant="ghost"
				size="sm"
				render={
					<Link to="/market/candles" search={{ symbol_id: row.id }} />
				}
			>
				<IconChartCandle />
				Ver velas
			</Button>
		),
	},
];

export function SymbolsPage() {
	usePageBreadcrumb([{ label: 'Mercado' }, { label: 'Símbolos' }]);
	const [exchangeId, setExchangeId] = useState<string>(ALL);
	const [assetClass, setAssetClass] = useState<string>(ALL);

	const exchangesQuery = useExchangesQuery({ is_active: true });
	const symbolsQuery = useSymbolsQuery({
		is_active: true,
		exchange_id: exchangeId === ALL ? undefined : Number(exchangeId),
		asset_class: assetClass === ALL ? undefined : (assetClass as AssetClass),
	});

	const exchangeOptions = [
		{ value: ALL, label: 'Todos los exchanges' },
		...(exchangesQuery.data ?? []).map((exchange) => ({
			value: String(exchange.id),
			label: exchange.name,
		})),
	];
	const classOptions = [{ value: ALL, label: 'Todas las clases' }, ...ASSET_CLASS_OPTIONS];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Símbolos"
				description="Activos disponibles para analizar y operar."
			/>
			<div className="grid gap-3 sm:grid-cols-2 lg:max-w-xl">
				<OptionSelect
					aria-label="Exchange"
					size="sm"
					value={exchangeId}
					onChange={(value) => setExchangeId(value ?? ALL)}
					options={exchangeOptions}
				/>
				<OptionSelect
					aria-label="Clase de activo"
					size="sm"
					value={assetClass}
					onChange={(value) => setAssetClass(value ?? ALL)}
					options={classOptions}
				/>
			</div>
			<DataTable
				columns={columns}
				rows={symbolsQuery.data}
				getRowId={(row) => row.id}
				isLoading={symbolsQuery.isLoading}
				error={symbolsQuery.error}
				errorTitle="No pudimos cargar los símbolos"
				empty="No hay símbolos activos con esos filtros."
			/>
		</div>
	);
}
