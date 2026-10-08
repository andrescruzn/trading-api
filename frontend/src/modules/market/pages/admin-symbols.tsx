import { IconPencil, IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { AssetClass, MarketSymbol } from '@/modules/market/api/market.api';
import { SymbolFormDialog } from '@/modules/market/components/symbol-form-dialog';
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

const STATUS_OPTIONS = [
	{ value: ALL, label: 'Todos los estados' },
	{ value: 'true', label: 'Activos' },
	{ value: 'false', label: 'Inactivos' },
];

export function AdminSymbolsPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Símbolos' }]);
	const [exchangeId, setExchangeId] = useState(ALL);
	const [assetClass, setAssetClass] = useState(ALL);
	const [status, setStatus] = useState(ALL);
	const [editing, setEditing] = useState<MarketSymbol | null | undefined>(
		undefined,
	);

	const exchangesQuery = useExchangesQuery();
	const symbolsQuery = useSymbolsQuery({
		exchange_id: exchangeId === ALL ? undefined : Number(exchangeId),
		asset_class: assetClass === ALL ? undefined : (assetClass as AssetClass),
		is_active: status === ALL ? undefined : status === 'true',
	});

	const columns: DataTableColumn<MarketSymbol>[] = [
		{
			id: 'id',
			header: 'ID',
			className: 'w-16 font-mono',
			cell: (row) => row.id,
		},
		{
			id: 'symbol',
			header: 'Símbolo',
			cell: (row) => (
				<span className="font-mono font-medium">{row.symbol}</span>
			),
		},
		{
			id: 'exchange',
			header: 'Exchange',
			cell: (row) => row.exchange_name ?? '—',
		},
		{
			id: 'class',
			header: 'Clase',
			cell: (row) => ASSET_CLASS_LABELS[row.asset_class] ?? row.asset_class,
		},
		{
			id: 'pair',
			header: 'Base / cotización',
			cell: (row) => `${row.base_asset ?? '—'} / ${row.quote_asset ?? '—'}`,
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => (
				<Badge variant={row.is_active ? 'secondary' : 'outline'}>
					{row.is_active ? 'Activo' : 'Inactivo'}
				</Badge>
			),
		},
		{
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) => (
				<Button variant="ghost" size="sm" onClick={() => setEditing(row)}>
					<IconPencil />
					Editar
				</Button>
			),
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Símbolos"
				description="Activos que el sistema descarga y puede operar."
				actions={[
					{
						label: 'Nuevo símbolo',
						icon: <IconPlus />,
						onClick: () => setEditing(null),
					},
				]}
			/>
			<div className="grid gap-3 sm:grid-cols-3 lg:max-w-3xl">
				<OptionSelect
					aria-label="Exchange"
					size="sm"
					value={exchangeId}
					onChange={(value) => setExchangeId(value ?? ALL)}
					options={[
						{ value: ALL, label: 'Todos los exchanges' },
						...(exchangesQuery.data ?? []).map((exchange) => ({
							value: String(exchange.id),
							label: exchange.name,
						})),
					]}
				/>
				<OptionSelect
					aria-label="Clase de activo"
					size="sm"
					value={assetClass}
					onChange={(value) => setAssetClass(value ?? ALL)}
					options={[
						{ value: ALL, label: 'Todas las clases' },
						...ASSET_CLASS_OPTIONS,
					]}
				/>
				<OptionSelect
					aria-label="Estado"
					size="sm"
					value={status}
					onChange={(value) => setStatus(value ?? ALL)}
					options={STATUS_OPTIONS}
				/>
			</div>
			<DataTable
				columns={columns}
				rows={symbolsQuery.data}
				getRowId={(row) => row.id}
				isLoading={symbolsQuery.isLoading}
				error={symbolsQuery.error}
				errorTitle="No pudimos cargar los símbolos"
				empty="No hay símbolos con esos filtros."
			/>
			<SymbolFormDialog
				open={editing !== undefined}
				onOpenChange={(open) => !open && setEditing(undefined)}
				symbol={editing ?? null}
			/>
		</div>
	);
}
