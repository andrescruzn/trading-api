import type { AlertEvent } from '@/modules/alerts/api/alerts.api';
import {
	DeliveryBadge,
	SeverityBadge,
} from '@/modules/alerts/components/alert-badges';
import { useAlertEventsQuery } from '@/modules/alerts/hooks/use-alerts-queries';
import { botLabel } from '@/modules/alerts/lib/alerts-labels';
import {
	useBotsQuery,
	useMyBotsQuery,
} from '@/modules/bots/hooks/use-bots-queries';
import { useSymbolsQuery } from '@/modules/market/hooks/use-market-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { formatDateTime } from '@/modules/shared/lib/format';

type AlertEventsTableProps = {
	/** `admin` muestra usuario y bot; `user` muestra el mensaje. */
	variant: 'user' | 'admin';
};

const EMPTY_CELL = <span className="text-muted-foreground">—</span>;

/**
 * Historial de eventos de alerta. Vive dentro de su pestaña: la consulta solo
 * corre cuando la pestaña se abre (Base UI no monta los paneles ocultos).
 */
export function AlertEventsTable({ variant }: AlertEventsTableProps) {
	const isAdmin = variant === 'admin';
	const eventsQuery = useAlertEventsQuery({ limit: isAdmin ? 200 : 100 });
	// Admin ve los bots de todos; un usuario solo puede listar los suyos.
	const allBotsQuery = useBotsQuery({}, { enabled: isAdmin });
	const myBotsQuery = useMyBotsQuery({ enabled: !isAdmin });
	const botsQuery = isAdmin ? allBotsQuery : myBotsQuery;
	const symbolsQuery = useSymbolsQuery();

	const baseColumns: DataTableColumn<AlertEvent>[] = [
		{
			id: 'ts',
			header: 'Fecha',
			className: 'whitespace-nowrap',
			cell: (row) => formatDateTime(row.ts),
			skeletonClassName: 'w-32',
		},
		{
			id: 'title',
			header: 'Título',
			cell: (row) => <span className="font-medium">{row.title}</span>,
			skeletonClassName: 'w-40',
		},
		{
			id: 'severity',
			header: 'Severidad',
			cell: (row) => <SeverityBadge severity={row.severity} />,
		},
		{
			id: 'delivery',
			header: 'Entrega',
			cell: (row) => <DeliveryBadge status={row.delivery_status} />,
		},
	];

	const extraColumns: DataTableColumn<AlertEvent>[] = isAdmin
		? [
				{
					id: 'user',
					header: 'Usuario',
					cell: (row) => (row.user_id ? `Usuario #${row.user_id}` : EMPTY_CELL),
				},
				{
					id: 'bot',
					header: 'Bot',
					cell: (row) =>
						row.bot_id
							? botLabel(row.bot_id, botsQuery.data, symbolsQuery.data)
							: EMPTY_CELL,
				},
			]
		: [
				{
					id: 'message',
					header: 'Mensaje',
					cell: (row) =>
						row.message ? (
							<span className="line-clamp-2 max-w-md whitespace-normal text-muted-foreground">
								{row.message}
							</span>
						) : (
							EMPTY_CELL
						),
					skeletonClassName: 'w-48',
				},
			];

	return (
		<DataTable
			columns={[...baseColumns, ...extraColumns]}
			rows={eventsQuery.data}
			getRowId={(row) => row.id}
			isLoading={eventsQuery.isLoading}
			error={eventsQuery.error}
			errorTitle="No pudimos cargar los eventos de alerta"
			empty={
				isAdmin
					? 'Aún no se ha disparado ninguna alerta.'
					: 'Aún no recibes alertas. Aparecerán aquí cuando se cumpla alguna de tus reglas.'
			}
		/>
	);
}
