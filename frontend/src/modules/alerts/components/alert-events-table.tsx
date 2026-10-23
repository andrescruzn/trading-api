import type { AlertEvent } from '@/modules/alerts/api/alerts.api';
import {
	DeliveryBadge,
	SeverityBadge,
} from '@/modules/alerts/components/alert-badges';
import { useAlertEventsPageQuery } from '@/modules/alerts/hooks/use-alerts-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { useServerPagination } from '@/modules/shared/hooks/use-server-pagination';
import { formatDateTime } from '@/modules/shared/lib/format';

const EMPTY_CELL = <span className="text-muted-foreground">—</span>;

/**
 * Historial de eventos de alerta, paginado en el servidor (las reglas
 * periódicas generan eventos sin parar). Vive dentro de su pestaña: la
 * consulta solo corre cuando la pestaña se abre (Base UI no monta los paneles
 * ocultos).
 */
export function AlertEventsTable() {
	const { params, tablePagination } = useServerPagination('');
	const eventsQuery = useAlertEventsPageQuery({}, params);

	const columns: DataTableColumn<AlertEvent>[] = [
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
			columns={columns}
			rows={eventsQuery.data?.items}
			getRowId={(row) => row.id}
			isLoading={eventsQuery.isLoading}
			isFetching={eventsQuery.isPlaceholderData}
			pagination={tablePagination(eventsQuery.data)}
			error={eventsQuery.error}
			errorTitle="No pudimos cargar los eventos de alerta"
			empty="Aún no recibes alertas. Aparecerán aquí cuando se cumpla alguna de tus reglas."
		/>
	);
}
