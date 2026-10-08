import {
	IconBell,
	IconBellOff,
	IconDots,
	IconLoader2,
	IconPencil,
	IconPlus,
} from '@tabler/icons-react';
import { useState } from 'react';
import type { AlertRule } from '@/modules/alerts/api/alerts.api';
import {
	ChannelsList,
	RuleStatusBadge,
	RuleTypeBadge,
} from '@/modules/alerts/components/alert-badges';
import { AlertEventsTable } from '@/modules/alerts/components/alert-events-table';
import { AlertRuleFormDialog } from '@/modules/alerts/components/alert-rule-form-dialog';
import { useUpdateAlertRuleMutation } from '@/modules/alerts/hooks/use-alerts-mutations';
import { useAlertRulesQuery } from '@/modules/alerts/hooks/use-alerts-queries';
import { botLabel } from '@/modules/alerts/lib/alerts-labels';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useMyBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { useSymbolsQuery } from '@/modules/market/hooks/use-market-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDate } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from '@/modules/ui/components/alert-dialog';
import { Button } from '@/modules/ui/components/button';
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
} from '@/modules/ui/components/dropdown-menu';
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from '@/modules/ui/components/tabs';
import { toast } from '@/modules/ui/components/toast';

export function AlertsPage() {
	usePageBreadcrumb([{ label: 'Alertas' }]);
	const rulesQuery = useAlertRulesQuery();
	const botsQuery = useMyBotsQuery();
	const symbolsQuery = useSymbolsQuery();
	const updateMutation = useUpdateAlertRuleMutation();
	// `undefined` = diálogo cerrado; `null` = crear; una regla = editar.
	const [editing, setEditing] = useState<AlertRule | null | undefined>(
		undefined,
	);
	const [deactivating, setDeactivating] = useState<AlertRule | null>(null);

	function setRuleActive(rule: AlertRule, isActive: boolean) {
		updateMutation.mutate(
			{ id: rule.id, input: { is_active: isActive } },
			{
				onSuccess: () => {
					toast.add({
						title: isActive ? 'Regla activada' : 'Regla desactivada',
						type: 'success',
					});
					setDeactivating(null);
				},
				onError: (error) =>
					toast.add({
						title: isActive
							? 'No pudimos activar la regla'
							: 'No pudimos desactivar la regla',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	const columns: DataTableColumn<AlertRule>[] = [
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
			id: 'bot',
			header: 'Bot',
			cell: (row) =>
				row.bot_id ? (
					botLabel(row.bot_id, botsQuery.data, symbolsQuery.data)
				) : (
					<span className="text-muted-foreground">Cualquier bot</span>
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
		{
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) => (
				<DropdownMenu>
					<DropdownMenuTrigger
						render={<Button variant="ghost" size="icon-sm" />}
					>
						<IconDots />
						<span className="sr-only">Acciones de {row.name}</span>
					</DropdownMenuTrigger>
					<DropdownMenuContent align="end" className="w-auto min-w-40">
						<DropdownMenuItem onClick={() => setEditing(row)}>
							<IconPencil />
							Editar
						</DropdownMenuItem>
						{row.is_active ? (
							<DropdownMenuItem
								variant="destructive"
								onClick={() => setDeactivating(row)}
							>
								<IconBellOff />
								Desactivar
							</DropdownMenuItem>
						) : (
							<DropdownMenuItem
								disabled={updateMutation.isPending}
								onClick={() => setRuleActive(row, true)}
							>
								<IconBell />
								Activar
							</DropdownMenuItem>
						)}
					</DropdownMenuContent>
				</DropdownMenu>
			),
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Alertas"
				description="Elige qué eventos te avisan y por qué canal, y revisa las alertas que recibiste."
				actions={[
					{
						label: 'Nueva regla',
						icon: <IconPlus />,
						onClick: () => setEditing(null),
					},
				]}
			/>
			<Tabs defaultValue="rules">
				<TabsList>
					<TabsTrigger value="rules">Mis reglas</TabsTrigger>
					<TabsTrigger value="events">Historial</TabsTrigger>
				</TabsList>
				<TabsContent value="rules" className="pt-2">
					<DataTable
						columns={columns}
						rows={rulesQuery.data}
						getRowId={(row) => row.id}
						isLoading={rulesQuery.isLoading}
						error={rulesQuery.error}
						errorTitle="No pudimos cargar tus reglas de alerta"
						empty="Aún no tienes reglas de alerta. Crea una para recibir avisos de tus bots."
					/>
				</TabsContent>
				<TabsContent value="events" className="pt-2">
					<AlertEventsTable variant="user" />
				</TabsContent>
			</Tabs>

			<AlertRuleFormDialog
				open={editing !== undefined}
				onOpenChange={(open) => !open && setEditing(undefined)}
				rule={editing ?? null}
			/>

			<AlertDialog
				open={!!deactivating}
				onOpenChange={(open) => !open && setDeactivating(null)}
			>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>
							¿Desactivar la regla «{deactivating?.name}»?
						</AlertDialogTitle>
						<AlertDialogDescription>
							Dejarás de recibir sus avisos. Puedes activarla de nuevo cuando
							quieras.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel>Cancelar</AlertDialogCancel>
						<AlertDialogAction
							variant="destructive"
							disabled={updateMutation.isPending}
							onClick={() => deactivating && setRuleActive(deactivating, false)}
						>
							{updateMutation.isPending && (
								<IconLoader2 className="animate-spin" />
							)}
							Desactivar regla
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</div>
	);
}
