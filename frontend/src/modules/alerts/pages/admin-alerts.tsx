import { IconBrandTelegram } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
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
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import { useOwners } from '@/modules/auth/hooks/use-users-queries';
import { useBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { useSymbolsQuery } from '@/modules/market/hooks/use-market-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDate } from '@/modules/shared/lib/format';
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from '@/modules/ui/components/tabs';

const ALL = 'all';

export function AdminAlertsPage() {
	usePageBreadcrumb([
		{ label: 'Administración' },
		{ label: 'Todas las alertas' },
	]);
	const rulesQuery = useAlertRulesQuery();
	const botsQuery = useBotsQuery();
	const symbolsQuery = useSymbolsQuery();
	const owners = useOwners(ALL);
	const [owner, setOwner] = useState(ALL);
	const ownerId = owner === ALL ? undefined : Number(owner);

	const rules = rulesQuery.data?.filter(
		(rule) => ownerId === undefined || rule.user_id === ownerId,
	);

	const columns: DataTableColumn<AlertRule>[] = [
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
			skeletonClassName: 'w-36',
		},
		{
			id: 'type',
			header: 'Tipo',
			cell: (row) => <RuleTypeBadge type={row.rule_type} />,
		},
		{
			id: 'owner',
			header: 'Dueño',
			cell: (row) => <OwnerCell userId={row.user_id} users={owners.byId} />,
		},
		{
			id: 'bot',
			header: 'Agente',
			cell: (row) =>
				row.bot_id ? (
					botLabel(row.bot_id, botsQuery.data, symbolsQuery.data)
				) : (
					<span className="text-muted-foreground">Cualquier agente</span>
				),
		},
		{
			id: 'channels',
			header: 'Canales',
			cell: (row) => <ChannelsList channels={row.channels} />,
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => <RuleStatusBadge isActive={row.is_active} />,
		},
		{
			id: 'created',
			header: 'Creada',
			cell: (row) => formatDate(row.created_at),
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Todas las alertas"
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
			<div className="grid gap-3 sm:max-w-xs">
				<OptionSelect
					aria-label="Dueño"
					size="sm"
					value={owner}
					onChange={(value) => setOwner(value ?? ALL)}
					options={owners.options}
				/>
			</div>
			<Tabs defaultValue="rules">
				<TabsList>
					<TabsTrigger value="rules">Reglas</TabsTrigger>
					<TabsTrigger value="events">Eventos</TabsTrigger>
				</TabsList>
				<TabsContent value="rules" className="pt-2">
					<DataTable
						columns={columns}
						rows={rules}
						getRowId={(row) => row.id}
						isLoading={rulesQuery.isLoading}
						error={rulesQuery.error}
						errorTitle="No pudimos cargar las reglas de alerta"
						empty={
							ownerId === undefined
								? 'Aún no hay reglas de alerta. Cada usuario crea las suyas desde Alertas.'
								: 'Este usuario aún no tiene reglas de alerta.'
						}
					/>
				</TabsContent>
				<TabsContent value="events" className="pt-2">
					<AlertEventsTable
						variant="admin"
						users={owners.byId}
						ownerId={ownerId}
					/>
				</TabsContent>
			</Tabs>
		</div>
	);
}
