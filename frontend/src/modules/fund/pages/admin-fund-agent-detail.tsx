import {
	IconArrowLeft,
	IconCalculator,
	IconCash,
	IconChartLine,
	IconCoins,
	IconPlus,
	IconUsers,
	IconX,
} from '@tabler/icons-react';
import { getRouteApi, Link } from '@tanstack/react-router';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import { useOwners } from '@/modules/auth/hooks/use-users-queries';
import { BotStatusBadge } from '@/modules/bots/components/bot-badges';
import type {
	AgentSettlement,
	AllocationOrder,
	PoolParticipant,
	RedemptionRequest,
} from '@/modules/fund/api/fund.api';
import { QueueAllocationDialog } from '@/modules/fund/components/queue-allocation-dialog';
import { RedemptionRequestsTable } from '@/modules/fund/components/redemptions-tables';
import { SettleAgentDialog } from '@/modules/fund/components/settle-agent-dialog';
import { useCancelRedemptionMutation } from '@/modules/fund/hooks/use-fund-payouts-mutations';
import { useCancelAllocationMutation } from '@/modules/fund/hooks/use-fund-pools-mutations';
import { usePoolQuery } from '@/modules/fund/hooks/use-fund-pools-queries';
import { LEDGER_BUCKET_LABELS } from '@/modules/fund/lib/fund-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { StatCard } from '@/modules/shared/components/stat-card';
import {
	formatDateTime,
	formatNumber,
	formatPercent,
	formatSignedPrice,
} from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button } from '@/modules/ui/components/button';
import { Skeleton } from '@/modules/ui/components/skeleton';
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from '@/modules/ui/components/tabs';
import { toast } from '@/modules/ui/components/toast';
import { cn } from '@/modules/ui/lib/utils';

const ALL = 'all';
const routeApi = getRouteApi('/_app/admin/fund-agents/$poolId');

const SETTLEMENT_COLUMNS: DataTableColumn<AgentSettlement>[] = [
	{
		id: 'settled',
		header: 'Fecha',
		className: 'whitespace-nowrap',
		cell: (row) => formatDateTime(row.settled_at),
	},
	{
		id: 'result',
		header: 'Resultado',
		className: 'text-right tabular-nums',
		cell: (row) => {
			const value = Number(row.trading_result);
			return (
				<span className={cn(value >= 0 ? 'text-chart-1' : 'text-destructive')}>
					{formatSignedPrice(row.trading_result)}
				</span>
			);
		},
	},
	{
		id: 'nav',
		header: 'Valor unidad',
		className: 'text-right tabular-nums',
		cell: (row) => formatNumber(row.nav, 6),
	},
	{
		id: 'in',
		header: 'Entró',
		className: 'text-right tabular-nums',
		cell: (row) => formatNumber(row.allocated_amount, 2),
	},
	{
		id: 'out',
		header: 'Salió',
		className: 'text-right tabular-nums',
		cell: (row) => formatNumber(row.redeemed_amount, 2),
	},
	{
		id: 'fees',
		header: 'Comisión',
		className: 'text-right tabular-nums',
		cell: (row) => formatNumber(row.fees_total, 2),
	},
	{
		id: 'after',
		header: 'Saldo después',
		className: 'text-right tabular-nums font-medium',
		cell: (row) => formatNumber(row.equity_after, 2),
	},
	{
		id: 'note',
		header: 'Nota',
		className: 'max-w-60 truncate',
		cell: (row) => row.note ?? '—',
	},
];

export function AdminFundAgentDetailPage() {
	const { poolId } = routeApi.useParams();
	const id = Number(poolId);
	const poolQuery = usePoolQuery(Number.isInteger(id) && id > 0 ? id : null);
	const canManage = useCanManage();
	const owners = useOwners(ALL);
	const cancelMutation = useCancelAllocationMutation();
	const cancelRedemptionMutation = useCancelRedemptionMutation();
	const [allocating, setAllocating] = useState(false);
	const [settling, setSettling] = useState(false);
	const pool = poolQuery.data;

	usePageBreadcrumb([
		{ label: 'Administración' },
		{ label: 'Agentes del fondo', href: '/admin/fund-agents' },
		{ label: pool?.agent?.name ?? 'Agente' },
	]);

	function cancel(order: AllocationOrder) {
		cancelMutation.mutate(order.id, {
			onSuccess: () =>
				toast.add({ title: 'Asignación cancelada', type: 'success' }),
			onError: (error) =>
				toast.add({
					title: 'No pudimos cancelar la asignación',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	function cancelRedemption(request: RedemptionRequest) {
		cancelRedemptionMutation.mutate(request.id, {
			onSuccess: () => toast.add({ title: 'Salida anulada', type: 'success' }),
			onError: (error) =>
				toast.add({
					title: 'No pudimos anular la salida',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	if (poolQuery.isLoading) {
		return (
			<div className="flex flex-col gap-6">
				<Skeleton className="h-10 w-72" />
				<Skeleton className="h-32 w-full" />
			</div>
		);
	}
	if (!pool) {
		return (
			<div className="flex flex-col items-start gap-4">
				<ErrorAlert
					title="No pudimos abrir el agente del fondo"
					error={
						poolQuery.error ?? new Error('No encontramos ese agente del fondo.')
					}
				/>
				<Button variant="outline" render={<Link to="/admin/fund-agents" />}>
					<IconArrowLeft />
					Volver a los agentes del fondo
				</Button>
			</div>
		);
	}

	const participantColumns: DataTableColumn<PoolParticipant>[] = [
		{
			id: 'user',
			header: 'Persona',
			cell: (row) => <OwnerCell userId={row.user_id} users={owners.byId} />,
		},
		{
			id: 'units',
			header: 'Unidades',
			className: 'text-right tabular-nums',
			cell: (row) => formatNumber(row.units, 4),
		},
		{
			id: 'share',
			header: 'Participación',
			className: 'text-right tabular-nums',
			cell: (row) => formatPercent(row.share),
		},
		{
			id: 'cost',
			header: 'Aportó',
			className: 'text-right tabular-nums',
			cell: (row) => formatNumber(row.cost, 2),
		},
		{
			id: 'value',
			header: 'Vale (última liquidación)',
			className: 'text-right tabular-nums font-medium',
			cell: (row) => formatNumber(row.value, 2),
		},
		{
			id: 'since',
			header: 'Desde',
			className: 'whitespace-nowrap',
			cell: (row) => formatDateTime(row.first_acquired_at),
		},
	];

	const queueColumns: DataTableColumn<AllocationOrder>[] = [
		{
			id: 'created',
			header: 'En cola desde',
			className: 'whitespace-nowrap',
			cell: (row) => formatDateTime(row.created_at),
		},
		{
			id: 'user',
			header: 'Persona',
			cell: (row) => <OwnerCell userId={row.user_id} users={owners.byId} />,
		},
		{
			id: 'source',
			header: 'Sale de',
			cell: (row) => LEDGER_BUCKET_LABELS[row.source_bucket],
		},
		{
			id: 'amount',
			header: 'Monto',
			className: 'text-right tabular-nums font-medium',
			cell: (row) => `${formatNumber(row.amount, 2)} ${pool.asset}`,
		},
		...(canManage
			? [
					{
						id: 'actions',
						header: <span className="sr-only">Acciones</span>,
						className: 'text-right',
						cell: (row: AllocationOrder) => (
							<Button
								variant="ghost"
								size="sm"
								disabled={cancelMutation.isPending}
								onClick={() => cancel(row)}
							>
								<IconX />
								Cancelar
							</Button>
						),
					},
				]
			: []),
	];

	return (
		<div className="flex flex-col gap-6">
			<header className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
				<div className="flex flex-col gap-2">
					<h1 className="text-2xl font-semibold tracking-tight">
						{pool.agent?.name ?? `Agente #${pool.bot_id}`}
					</h1>
					<div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
						{pool.agent && <BotStatusBadge status={pool.agent.status} />}
						<span className="font-mono text-foreground">
							{pool.agent?.symbol}
						</span>
						<span aria-hidden>·</span>
						<Link
							to="/agents/$agentId"
							params={{ agentId: String(pool.bot_id) }}
							className="underline-offset-4 hover:underline"
						>
							Ver el agente
						</Link>
					</div>
				</div>
				{canManage && (
					<div className="flex flex-wrap gap-2">
						<Button variant="outline" onClick={() => setAllocating(true)}>
							<IconPlus />
							Asignar dinero
						</Button>
						<Button onClick={() => setSettling(true)}>
							<IconCalculator />
							Liquidar
						</Button>
					</div>
				)}
			</header>

			<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<StatCard
					label="Capital hoy"
					value={`${formatNumber(pool.estimated_capital, 2)} ${pool.asset}`}
					hint="Con lo abierto a precio de costo; con este monto se calcula el 1 %"
					icon={<IconCoins className="size-4" />}
				/>
				<StatCard
					label="Saldo liquidado"
					value={`${formatNumber(pool.equity, 2)} ${pool.asset}`}
					hint={
						pool.last_settled_at
							? `Liquidado el ${formatDateTime(pool.last_settled_at)}`
							: 'Aún sin liquidar'
					}
					icon={<IconCash className="size-4" />}
				/>
				<StatCard
					label="Valor de una unidad"
					value={formatNumber(pool.nav, 6)}
					hint={`${formatNumber(pool.units, 2)} unidades en circulación`}
					icon={<IconChartLine className="size-4" />}
				/>
				<StatCard
					label="Participantes"
					value={pool.participants}
					hint={
						Number(pool.queued_total) > 0
							? `${formatNumber(pool.queued_total, 2)} ${pool.asset} en cola`
							: 'Nada en cola'
					}
					icon={<IconUsers className="size-4" />}
				/>
			</div>

			<Tabs defaultValue="participants">
				<TabsList>
					<TabsTrigger value="participants">Participantes</TabsTrigger>
					<TabsTrigger value="queue">
						En cola ({pool.queued.length})
					</TabsTrigger>
					<TabsTrigger value="redemptions">
						Salidas en cola ({pool.queued_redemptions.length})
					</TabsTrigger>
					<TabsTrigger value="settlements">Liquidaciones</TabsTrigger>
				</TabsList>
				<TabsContent value="participants" className="pt-2">
					<DataTable
						columns={participantColumns}
						rows={pool.participants_detail}
						getRowId={(row) => row.user_id}
						isLoading={false}
						empty="Aún nadie tiene dinero en este agente. Asígnale dinero y liquídalo."
					/>
				</TabsContent>
				<TabsContent value="queue" className="pt-2">
					<DataTable
						columns={queueColumns}
						rows={pool.queued}
						getRowId={(row) => row.id}
						isLoading={false}
						empty="No hay asignaciones en cola."
					/>
				</TabsContent>
				<TabsContent value="redemptions" className="pt-2">
					<RedemptionRequestsTable
						rows={pool.queued_redemptions}
						isLoading={false}
						users={owners.byId}
						empty="Nadie pidió sacar dinero de este agente."
						onCancel={canManage ? cancelRedemption : undefined}
						isCanceling={cancelRedemptionMutation.isPending}
					/>
				</TabsContent>
				<TabsContent value="settlements" className="pt-2">
					<DataTable
						columns={SETTLEMENT_COLUMNS}
						rows={pool.settlements}
						getRowId={(row) => row.id}
						isLoading={false}
						empty="Este agente aún no se ha liquidado."
					/>
				</TabsContent>
			</Tabs>

			<QueueAllocationDialog
				pool={allocating ? pool : null}
				onClose={() => setAllocating(false)}
			/>
			<SettleAgentDialog
				pool={settling ? pool : null}
				onClose={() => setSettling(false)}
			/>
		</div>
	);
}
