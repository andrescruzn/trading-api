import { IconPencil, IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { Exchange } from '@/modules/market/api/market.api';
import { ExchangeFormDialog } from '@/modules/market/components/exchange-form-dialog';
import { useExchangesQuery } from '@/modules/market/hooks/use-market-queries';
import { EXCHANGE_TYPE_LABELS } from '@/modules/market/lib/market-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDate } from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';

export function AdminExchangesPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Exchanges' }]);
	const exchangesQuery = useExchangesQuery();
	// `undefined` = diálogo cerrado; `null` = crear; un exchange = editar.
	const [editing, setEditing] = useState<Exchange | null | undefined>(
		undefined,
	);

	const columns: DataTableColumn<Exchange>[] = [
		{
			id: 'id',
			header: 'ID',
			className: 'w-16 font-mono',
			cell: (row) => row.id,
		},
		{
			id: 'name',
			header: 'Nombre',
			cell: (row) => <span className="font-medium">{row.name}</span>,
		},
		{
			id: 'type',
			header: 'Tipo',
			cell: (row) => EXCHANGE_TYPE_LABELS[row.type] ?? row.type,
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
			id: 'created',
			header: 'Creado',
			cell: (row) => formatDate(row.created_at),
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
				title="Exchanges"
				description="Exchanges, brókers y proveedores de datos."
				actions={[
					{
						label: 'Nuevo exchange',
						icon: <IconPlus />,
						onClick: () => setEditing(null),
					},
				]}
			/>
			<DataTable
				columns={columns}
				rows={exchangesQuery.data}
				getRowId={(row) => row.id}
				isLoading={exchangesQuery.isLoading}
				error={exchangesQuery.error}
				errorTitle="No pudimos cargar los exchanges"
				empty="Aún no hay exchanges. Crea el primero."
			/>
			<ExchangeFormDialog
				open={editing !== undefined}
				onOpenChange={(open) => !open && setEditing(undefined)}
				exchange={editing ?? null}
			/>
		</div>
	);
}
