import type { ReactNode } from 'react';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { formatDate } from '@/modules/shared/lib/format';
import type { Strategy } from '@/modules/strategies/api/strategies.api';
import { StrategyRegimeBadge } from '@/modules/strategies/components/strategy-regime-badge';
import { strategyTypeLabel } from '@/modules/strategies/lib/strategies-labels';
import { Badge } from '@/modules/ui/components/badge';

type StrategiesTableProps = {
	rows: Strategy[] | undefined;
	isLoading: boolean;
	error: unknown;
	empty: ReactNode;
	onRowClick?: (strategy: Strategy) => void;
	/** Botones de la última columna; deben frenar la propagación del clic. */
	renderActions?: (strategy: Strategy) => ReactNode;
};

const baseColumns: DataTableColumn<Strategy>[] = [
	{
		id: 'name',
		header: 'Nombre',
		cell: (row) => <span className="font-medium">{row.name}</span>,
		skeletonClassName: 'w-36',
	},
	{
		id: 'version',
		header: 'Versión',
		className: 'font-mono',
		cell: (row) => row.version,
	},
	{
		id: 'type',
		header: 'Tipo',
		cell: (row) =>
			row.parameters?.strategy_type ? (
				<Badge variant="outline">
					{strategyTypeLabel(row.parameters.strategy_type)}
				</Badge>
			) : (
				'—'
			),
		skeletonClassName: 'w-32',
	},
	{
		id: 'regime',
		header: 'Régimen',
		cell: (row) => (
			<StrategyRegimeBadge regime={row.parameters?.regime_required} />
		),
	},
	{
		id: 'timeframe',
		header: 'Timeframe',
		className: 'font-mono',
		cell: (row) => row.parameters?.timeframe_code || '—',
	},
	{
		id: 'rules',
		header: 'Reglas',
		className: 'text-right tabular-nums',
		cell: (row) => row.parameters?.rules?.length ?? 0,
	},
	{
		id: 'created',
		header: 'Creada',
		cell: (row) => formatDate(row.created_at),
	},
];

/** Listado de estrategias compartido por la vista de usuario y la de admin. */
export function StrategiesTable({
	rows,
	isLoading,
	error,
	empty,
	onRowClick,
	renderActions,
}: StrategiesTableProps) {
	const columns: DataTableColumn<Strategy>[] = renderActions
		? [
				...baseColumns,
				{
					id: 'actions',
					header: <span className="sr-only">Acciones</span>,
					className: 'text-right',
					cell: renderActions,
				},
			]
		: baseColumns;

	return (
		<DataTable
			columns={columns}
			rows={rows}
			getRowId={(row) => row.id}
			isLoading={isLoading}
			error={error}
			errorTitle="No pudimos cargar las estrategias"
			empty={empty}
			onRowClick={onRowClick}
		/>
	);
}
