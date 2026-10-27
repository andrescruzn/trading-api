import type { BotHistoryEntry } from '@/modules/bots/api/bots.api';
import { useBotHistoryQuery } from '@/modules/bots/hooks/use-bots-queries';
import { describeHistoryEntry } from '@/modules/bots/lib/bot-history-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { useServerPagination } from '@/modules/shared/hooks/use-server-pagination';
import { formatDateTime } from '@/modules/shared/lib/format';

const columns: DataTableColumn<BotHistoryEntry>[] = [
	{
		id: 'ts',
		header: 'Fecha',
		className: 'whitespace-nowrap',
		cell: (row) => formatDateTime(row.ts),
		skeletonClassName: 'w-32',
	},
	{
		id: 'who',
		header: 'Quién',
		cell: (row) =>
			row.user_name ?? <span className="text-muted-foreground">Sistema</span>,
		skeletonClassName: 'w-24',
	},
	{
		id: 'what',
		header: 'Qué pasó',
		className: 'whitespace-normal',
		cell: (row) => describeHistoryEntry(row),
		skeletonClassName: 'w-64',
	},
];

/**
 * Quién creó, editó, inició, pausó o detuvo el agente, y cuándo lo cambió el
 * sistema por su cuenta (pérdida máxima, cuenta del dueño desactivada).
 */
export function AgentHistoryTab({ botId }: { botId: number }) {
	const { params, tablePagination } = useServerPagination(String(botId));
	const historyQuery = useBotHistoryQuery(botId, params);

	return (
		<DataTable
			columns={columns}
			rows={historyQuery.data?.items}
			pagination={tablePagination(historyQuery.data)}
			isFetching={historyQuery.isPlaceholderData}
			getRowId={(row) => row.id}
			isLoading={historyQuery.isLoading}
			error={historyQuery.error}
			errorTitle="No pudimos cargar el historial"
			empty="Aún no hay cambios registrados en este agente."
		/>
	);
}
