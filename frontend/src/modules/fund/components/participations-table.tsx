import { BotStatusBadge } from '@/modules/bots/components/bot-badges';
import type { Participation } from '@/modules/fund/api/fund.api';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import {
	formatDateTime,
	formatNumber,
	formatPercent,
	formatSignedPrice,
} from '@/modules/shared/lib/format';
import { cn } from '@/modules/ui/lib/utils';

const COLUMNS: DataTableColumn<Participation>[] = [
	{
		id: 'agent',
		header: 'Agente',
		cell: (row) => (
			<div className="flex flex-col">
				<span className="font-medium">{row.agent?.name ?? '—'}</span>
				<span className="font-mono text-xs text-muted-foreground">
					{row.agent?.symbol ?? ''}
				</span>
			</div>
		),
	},
	{
		id: 'status',
		header: 'Estado',
		cell: (row) =>
			row.agent ? <BotStatusBadge status={row.agent.status} /> : '—',
	},
	{
		id: 'cost',
		header: 'Aportaste',
		className: 'text-right tabular-nums',
		cell: (row) => formatNumber(row.cost, 2),
	},
	{
		id: 'value',
		header: 'Vale hoy',
		className: 'text-right tabular-nums font-medium',
		cell: (row) => formatNumber(row.value, 2),
	},
	{
		id: 'result',
		header: 'Resultado',
		className: 'text-right tabular-nums',
		cell: (row) => {
			const result = Number(row.result);
			const cost = Number(row.cost);
			return (
				<span className={cn(result >= 0 ? 'text-chart-1' : 'text-destructive')}>
					{formatSignedPrice(row.result)}
					{cost > 0 && ` (${formatPercent(result / cost)})`}
				</span>
			);
		},
	},
	{
		id: 'settled',
		header: 'Valor a la liquidación del',
		className: 'whitespace-nowrap',
		cell: (row) => formatDateTime(row.last_settled_at),
	},
];

type ParticipationsTableProps = {
	rows: Participation[] | undefined;
	isLoading: boolean;
	error: unknown;
};

/**
 * En qué agentes está el dinero de la persona y cuánto vale. El valor es el
 * de la última liquidación (exacto); entre liquidaciones el agente puede ir
 * ganando o perdiendo.
 */
export function ParticipationsTable({
	rows,
	isLoading,
	error,
}: ParticipationsTableProps) {
	return (
		<DataTable
			columns={COLUMNS}
			rows={rows}
			getRowId={(row) => row.pool_id}
			isLoading={isLoading}
			error={error}
			errorTitle="No pudimos cargar tus agentes"
			empty="Tu dinero aún no está en ningún agente. Los super admin lo asignan en la próxima liquidación."
		/>
	);
}
