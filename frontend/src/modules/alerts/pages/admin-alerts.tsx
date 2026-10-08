import { IconBrandTelegram } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import type { AlertRule } from '@/modules/alerts/api/alerts.api';
import {
	ChannelsList,
	RuleStatusBadge,
	RuleTypeBadge,
} from '@/modules/alerts/components/alert-badges';
import { AlertEventsTable } from '@/modules/alerts/components/alert-events-table';
import { useAlertRulesQuery } from '@/modules/alerts/hooks/use-alerts-queries';
import { botLabel } from '@/modules/alerts/lib/alerts-labels';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { useSymbolsQuery } from '@/modules/market/hooks/use-market-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDate } from '@/modules/shared/lib/format';
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from '@/modules/ui/components/tabs';

const EMPTY_CELL = <span className="text-muted-foreground">—</span>;

export function AdminAlertsPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Alertas' }]);
	const rulesQuery = useAlertRulesQuery();
	const botsQuery = useBotsQuery();
	const symbolsQuery = useSymbolsQuery();

	const columns: DataTableColumn<AlertRule>[] = [
		{ id: 'id', header: 'ID', className: 'w-16 font-mono', cell: (row) => row.id },
		{
			id: 'name',
			header: 'Nombre',
			cell: (row) => <span className="font-medium">{row.name}</span>,
			skeletonClassName: 'w-36',
		},
		{ id: 'type', header: 'Tipo', cell: (row) => <RuleTypeBadge type={row.rule_type} /> },
		{
			id: 'user',
			header: 'Usuario',
			cell: (row) => (row.user_id ? `Usuario #${row.user_id}` : EMPTY_CELL),
		},
		{
			id: 'bot',
			header: 'Bot',
			cell: (row) =>
				row.bot_id ? (
					botLabel(row.bot_id, botsQuery.data, symbolsQuery.data)
				) : (
					<span className="text-muted-foreground">Cualquier bot</span>
				),
		},
		{ id: 'channels', header: 'Canales', cell: (row) => <ChannelsList channels={row.channels} /> },
		{ id: 'status', header: 'Estado', cell: (row) => <RuleStatusBadge isActive={row.is_active} /> },
		{ id: 'created', header: 'Creada', cell: (row) => formatDate(row.created_at) },
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Alertas"
				description="Reglas y eventos de alerta de todos los usuarios. Solo lectura."
				actions={[
					{
						label: 'Configurar Telegram',
						icon: <IconBrandTelegram />,
						variant: 'outline',
						render: <Link to="/admin/telegram" />,
					},
				]}
			/>
			<Tabs defaultValue="rules">
				<TabsList>
					<TabsTrigger value="rules">Reglas</TabsTrigger>
					<TabsTrigger value="events">Eventos</TabsTrigger>
				</TabsList>
				<TabsContent value="rules" className="pt-2">
					<DataTable
						columns={columns}
						rows={rulesQuery.data}
						getRowId={(row) => row.id}
						isLoading={rulesQuery.isLoading}
						error={rulesQuery.error}
						errorTitle="No pudimos cargar las reglas de alerta"
						empty="Aún no hay reglas de alerta. Cada usuario crea las suyas desde Alertas."
					/>
				</TabsContent>
				<TabsContent value="events" className="pt-2">
					<AlertEventsTable variant="admin" />
				</TabsContent>
			</Tabs>
		</div>
	);
}
