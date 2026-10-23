import { IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import type { FeatureSet } from '@/modules/features/api/features.api';
import { FeatureSetFormDialog } from '@/modules/features/components/feature-set-form-dialog';
import { useFeatureSetsQuery } from '@/modules/features/hooks/use-features-queries';
import {
	FEATURE_SET_FOCUS_LABELS,
	INDICATOR_GROUP_LABELS,
} from '@/modules/features/lib/features-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDate } from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';

const columns: DataTableColumn<FeatureSet>[] = [
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
		id: 'focus',
		header: 'Enfoque',
		cell: (row) => FEATURE_SET_FOCUS_LABELS[row.focus] ?? row.focus,
	},
	{
		id: 'indicators',
		header: 'Indicadores',
		cell: (row) => (
			<span className="flex flex-wrap gap-1">
				{row.indicators.map((group) => (
					<Badge key={group} variant="outline">
						{INDICATOR_GROUP_LABELS[group] ?? group}
					</Badge>
				))}
			</span>
		),
		skeletonClassName: 'w-40',
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
	{
		id: 'created',
		header: 'Creado',
		cell: (row) => formatDate(row.created_at),
	},
];

export function AdminFeatureSetsPage() {
	const canManage = useCanManage();
	usePageBreadcrumb([
		{ label: 'Administración' },
		{ label: 'Conjuntos de indicadores' },
	]);
	const featureSetsQuery = useFeatureSetsQuery();
	const [creating, setCreating] = useState(false);

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Conjuntos de indicadores"
				description="Qué indicadores calcula cada agente. El spec usa {focus, indicators} con los grupos rsi, ema, macd, atr, bbands y vol_rel. El cálculo se hace por agente: solo, mientras está activo, o con Actualizar datos en su pestaña Mercado."
				actions={[
					{
						label: 'Nuevo conjunto',
						icon: <IconPlus />,
						onClick: () => setCreating(true),
						hidden: !canManage,
					},
				]}
			/>
			<DataTable
				columns={columns}
				rows={featureSetsQuery.data}
				getRowId={(row) => row.id}
				isLoading={featureSetsQuery.isLoading}
				error={featureSetsQuery.error}
				errorTitle="No pudimos cargar los conjuntos de indicadores"
				empty="Aún no hay conjuntos de indicadores. Crea uno o carga los de ejemplo con el seed feature_sets."
			/>
			<FeatureSetFormDialog open={creating} onOpenChange={setCreating} />
		</div>
	);
}
