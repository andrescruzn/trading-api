import type { ReactNode } from 'react';
import type { Candle } from '@/modules/market/api/market.api';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { formatDateTime, formatNumber } from '@/modules/shared/lib/format';

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
			header: {
				open: 'Apertura',
				high: 'Máximo',
				low: 'Mínimo',
				close: 'Cierre',
			}[key],
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

type CandlesTableProps = {
	rows: Candle[] | undefined;
	isLoading: boolean;
	error: unknown;
	empty: ReactNode;
};

/** Velas OHLCV de la más reciente a la más antigua. */
export function CandlesTable({
	rows,
	isLoading,
	error,
	empty,
}: CandlesTableProps) {
	return (
		<DataTable
			columns={columns}
			rows={rows}
			getRowId={(row) => row.id}
			isLoading={isLoading}
			error={error}
			errorTitle="No pudimos cargar las velas"
			empty={empty}
		/>
	);
}
