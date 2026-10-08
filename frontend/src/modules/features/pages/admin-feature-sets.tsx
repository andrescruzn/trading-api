import { IconCpu, IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { FeatureSet } from '@/modules/features/api/features.api';
import { CalculateFeaturesDialog } from '@/modules/features/components/calculate-features-dialog';
import { FeatureSetFormDialog } from '@/modules/features/components/feature-set-form-dialog';
import { useFeatureSetsQuery } from '@/modules/features/hooks/use-features-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDate } from '@/modules/shared/lib/format';

const columns: DataTableColumn<FeatureSet>[] = [
	{ id: 'id', header: 'ID', className: 'w-16 font-mono', cell: (row) => row.id },
	{
		id: 'name',
		header: 'Nombre',
		cell: (row) => <span className="font-medium">{row.name}</span>,
	},
	{
		id: 'version',
		header: 'Versión',
		className: 'font-mono',
		cell: (row) => row.version,
	},
	{
		id: 'description',
		header: 'Descripción',
		className: 'max-w-64 truncate',
		cell: (row) => row.description || '—',
	},
	{
		id: 'spec',
		header: 'Configuración',
		cell: (row) => {
			const spec = JSON.stringify(row.spec ?? {});
			return (
				<code
					title={spec}
					className="block max-w-72 truncate font-mono text-xs text-muted-foreground"
				>
					{spec}
				</code>
			);
		},
		skeletonClassName: 'w-40',
	},
	{ id: 'created', header: 'Creado', cell: (row) => formatDate(row.created_at) },
];

export function AdminFeatureSetsPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Feature sets' }]);
	const featureSetsQuery = useFeatureSetsQuery();
	const [creating, setCreating] = useState(false);
	const [calculating, setCalculating] = useState(false);

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Feature sets"
				description="Conjuntos de indicadores técnicos que se calculan sobre las velas."
				actions={[
					{
						label: 'Nuevo feature set',
						icon: <IconPlus />,
						onClick: () => setCreating(true),
					},
					{
						label: 'Calcular indicadores',
						icon: <IconCpu />,
						variant: 'outline',
						onClick: () => setCalculating(true),
					},
				]}
			/>
			<DataTable
				columns={columns}
				rows={featureSetsQuery.data}
				getRowId={(row) => row.id}
				isLoading={featureSetsQuery.isLoading}
				error={featureSetsQuery.error}
				errorTitle="No pudimos cargar los feature sets"
				empty="Aún no hay feature sets. Crea uno para poder calcular indicadores."
			/>
			<FeatureSetFormDialog open={creating} onOpenChange={setCreating} />
			<CalculateFeaturesDialog open={calculating} onOpenChange={setCalculating} />
		</div>
	);
}
