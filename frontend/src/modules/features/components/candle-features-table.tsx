import type { ReactNode } from 'react';
import type { CandleFeature } from '@/modules/features/api/features.api';
import { RegimeBadge } from '@/modules/features/components/regime-badge';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { formatDateTime, formatNumber } from '@/modules/shared/lib/format';

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

type CandleFeaturesTableProps = {
	rows: CandleFeature[] | undefined;
	isLoading: boolean;
	error: unknown;
	empty: ReactNode;
};

/** Indicadores calculados por vela, de la más reciente a la más antigua. */
export function CandleFeaturesTable({
	rows,
	isLoading,
	error,
	empty,
}: CandleFeaturesTableProps) {
	return (
		<DataTable
			columns={columns}
			rows={rows}
			getRowId={(row) => row.id}
			isLoading={isLoading}
			error={error}
			errorTitle="No pudimos cargar los indicadores"
			empty={empty}
		/>
	);
}
