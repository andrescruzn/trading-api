import { IconPencil, IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { Investor } from '@/modules/billing/api/billing.api';
import { InvestorFormDialog } from '@/modules/billing/components/investor-form-dialog';
import { useInvestorsQuery } from '@/modules/billing/hooks/use-billing-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDate, formatPercent } from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';

export function AdminInvestorsPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Inversores' }]);
	const investorsQuery = useInvestorsQuery();
	// `undefined` = diálogo cerrado; `null` = crear; un inversor = editar.
	const [editing, setEditing] = useState<Investor | null | undefined>(undefined);

	const columns: DataTableColumn<Investor>[] = [
		{ id: 'id', header: 'ID', className: 'w-16 font-mono', cell: (row) => row.id },
		{
			id: 'user',
			header: 'Usuario',
			cell: (row) => <span className="font-medium">Usuario #{row.user_id}</span>,
		},
		{
			id: 'fee',
			header: 'Comisión de desempeño',
			className: 'text-right font-mono tabular-nums',
			cell: (row) => formatPercent(row.fee_pct),
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
		{ id: 'created', header: 'Creado', cell: (row) => formatDate(row.created_at) },
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
				title="Inversores"
				description="Perfiles de inversor y su comisión de desempeño."
				actions={[
					{ label: 'Nuevo inversor', icon: <IconPlus />, onClick: () => setEditing(null) },
				]}
			/>
			<DataTable
				columns={columns}
				rows={investorsQuery.data}
				getRowId={(row) => row.id}
				isLoading={investorsQuery.isLoading}
				error={investorsQuery.error}
				errorTitle="No pudimos cargar los inversores"
				empty="Aún no hay inversores. Crea el primero para asignarle cuentas gestionadas."
			/>
			<InvestorFormDialog
				open={editing !== undefined}
				onOpenChange={(open) => !open && setEditing(undefined)}
				investor={editing ?? null}
			/>
		</div>
	);
}
