import type { Signal } from '@/modules/bots/api/bots.api';
import {
	SignalActionBadge,
	SignalDecisionBadge,
} from '@/modules/bots/components/bot-badges';
import { useSignalsPageQuery } from '@/modules/bots/hooks/use-bots-queries';
import { formatRiskReward } from '@/modules/bots/lib/bots-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { useServerPagination } from '@/modules/shared/hooks/use-server-pagination';
import {
	formatDateTime,
	formatPercent,
	formatPrice,
} from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';

const columns: DataTableColumn<Signal>[] = [
	{
		id: 'ts',
		header: 'Fecha',
		cell: (row) => formatDateTime(row.ts),
		skeletonClassName: 'w-32',
	},
	{
		id: 'action',
		header: 'Acción',
		cell: (row) => <SignalActionBadge action={row.action} />,
	},
	{
		id: 'approved',
		header: 'Estado',
		cell: (row) => (
			<Badge variant={row.approved ? 'secondary' : 'destructive'}>
				{row.approved ? 'Aprobada' : 'Rechazada'}
			</Badge>
		),
	},
	{
		id: 'decision',
		header: 'Ejecución',
		cell: (row) => <SignalDecisionBadge status={row.decision_status} />,
	},
	{
		id: 'entry',
		header: 'Entrada',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatPrice(row.entry_price),
	},
	{
		id: 'sl',
		header: 'SL',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatPrice(row.stop_loss),
	},
	{
		id: 'tp',
		header: 'TP',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatPrice(row.take_profit),
	},
	{
		id: 'rr',
		header: 'R/R',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatRiskReward(row.rr_ratio),
	},
	{
		id: 'confidence',
		header: 'Confianza',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatPercent(row.confidence, 0),
	},
];

type SignalsTableProps = {
	botId: number;
	onSelect: (signal: Signal) => void;
};

/**
 * Historial de señales de un agente (la más reciente primero), paginado en el
 * servidor: un agente automático genera una señal por vela cerrada.
 */
export function SignalsTable({ botId, onSelect }: SignalsTableProps) {
	const { params, tablePagination } = useServerPagination(String(botId));
	const signalsQuery = useSignalsPageQuery({ bot_id: botId }, params);

	return (
		<DataTable
			columns={columns}
			rows={signalsQuery.data?.items}
			pagination={tablePagination(signalsQuery.data)}
			isFetching={signalsQuery.isPlaceholderData}
			getRowId={(row) => row.id}
			isLoading={signalsQuery.isLoading}
			error={signalsQuery.error}
			errorTitle="No pudimos cargar las señales"
			empty="Este agente aún no tiene señales. Usa «Analizar ahora» para generar la primera."
			onRowClick={onSelect}
		/>
	);
}
