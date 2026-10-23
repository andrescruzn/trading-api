import {
	IconAlertTriangle,
	IconArrowDownToArc,
	IconArrowUpFromArc,
	IconCircleCheck,
	IconClockHour4,
	IconCoins,
	IconRobot,
	IconWallet,
} from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import { useOwners } from '@/modules/auth/hooks/use-users-queries';
import { BotStatusBadge } from '@/modules/bots/components/bot-badges';
import type { FundPool } from '@/modules/fund/api/fund.api';
import type { ParticipantSummary } from '@/modules/fund/api/fund-overview.api';
import { useFundOverviewQuery } from '@/modules/fund/hooks/use-fund-overview-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { StatCard } from '@/modules/shared/components/stat-card';
import {
	formatDateTime,
	formatNumber,
	formatSignedPrice,
} from '@/modules/shared/lib/format';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { Skeleton } from '@/modules/ui/components/skeleton';
import { cn } from '@/modules/ui/lib/utils';

const ALL = 'all';

// Diferencias menores a esto son redondeos (USDT)
const TOLERANCE = 1;

function Line({
	label,
	value,
	strong,
	className,
}: {
	label: string;
	value: string;
	strong?: boolean;
	className?: string;
}) {
	return (
		<div
			className={cn(
				'flex items-center justify-between gap-4 text-sm',
				strong && 'border-t pt-2 font-semibold',
				className,
			)}
		>
			<span className={strong ? undefined : 'text-muted-foreground'}>
				{label}
			</span>
			<span className="tabular-nums">{value}</span>
		</div>
	);
}

function signed(value: string) {
	const number = Number(value);
	return (
		<span className={cn(number >= 0 ? 'text-chart-1' : 'text-destructive')}>
			{formatSignedPrice(value)}
		</span>
	);
}

/**
 * Resumen del fondo (staff): la billetera, a quién le pertenece cada peso
 * (conciliación), el capital de cada agente, lo que está por resolver y lo
 * que ganó cada propietario o socio.
 */
export function AdminFundOverviewPage() {
	usePageBreadcrumb([
		{ label: 'Administración' },
		{ label: 'Resumen del fondo' },
	]);
	const overviewQuery = useFundOverviewQuery();
	const owners = useOwners(ALL);
	const data = overviewQuery.data;
	const asset = data?.asset ?? 'USDT';
	const money = (value: string | null | undefined) =>
		value == null ? '—' : `${formatNumber(value, 2)} ${asset}`;

	const difference = data?.difference == null ? null : Number(data.difference);
	const balanced = difference !== null && Math.abs(difference) < TOLERANCE;

	const agentColumns: DataTableColumn<FundPool>[] = [
		{
			id: 'agent',
			header: 'Agente',
			cell: (row) => (
				<Link
					to="/admin/fund-agents/$poolId"
					params={{ poolId: String(row.id) }}
					className="font-medium underline-offset-4 hover:underline"
				>
					{row.agent?.name ?? `Agente #${row.bot_id}`}
				</Link>
			),
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) =>
				row.agent ? <BotStatusBadge status={row.agent.status} /> : '—',
		},
		{
			id: 'settled',
			header: 'Saldo liquidado',
			className: 'text-right tabular-nums',
			cell: (row) => formatNumber(row.equity, 2),
		},
		{
			id: 'capital',
			header: 'Capital hoy',
			className: 'text-right tabular-nums font-medium',
			cell: (row) => formatNumber(row.estimated_capital, 2),
		},
		{
			id: 'result',
			header: 'Desde la liquidación',
			className: 'text-right tabular-nums',
			cell: (row) =>
				signed(String(Number(row.estimated_capital) - Number(row.equity))),
		},
		{
			id: 'participants',
			header: 'Participantes',
			className: 'text-right tabular-nums',
			cell: (row) => row.participants,
		},
		{
			id: 'last',
			header: 'Última liquidación',
			className: 'whitespace-nowrap',
			cell: (row) => formatDateTime(row.last_settled_at),
		},
	];

	const ownerColumns: DataTableColumn<ParticipantSummary>[] = [
		{
			id: 'user',
			header: 'Persona',
			cell: (row) => <OwnerCell userId={row.user_id} users={owners.byId} />,
		},
		{
			id: 'commissions',
			header: 'Comisiones recibidas',
			className: 'text-right tabular-nums',
			cell: (row) => formatNumber(row.commissions, 2),
		},
		{
			id: 'realized',
			header: 'Ganancia realizada',
			className: 'text-right tabular-nums',
			cell: (row) =>
				signed(String(Number(row.realized_gain) - Number(row.fees_paid))),
		},
		{
			id: 'unrealized',
			header: 'En agentes (no realizada)',
			className: 'text-right tabular-nums',
			cell: (row) => signed(row.unrealized_gain),
		},
		{
			id: 'total',
			header: 'Total ganado',
			className: 'text-right tabular-nums font-medium',
			cell: (row) => signed(row.total_earned),
		},
		{
			id: 'invested',
			header: 'Invertido hoy',
			className: 'text-right tabular-nums',
			cell: (row) => formatNumber(row.in_agents_value, 2),
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Resumen del fondo"
				description="Cuánto hay en la billetera, de quién es cada peso y cuánto ganó cada propietario o socio. Los inversores no ven esta página."
			/>

			{overviewQuery.error && (
				<ErrorAlert
					title="No pudimos cargar el resumen"
					error={overviewQuery.error}
				/>
			)}

			<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<StatCard
					label="Billetera"
					value={money(data?.wallet?.total_value)}
					hint={
						data?.wallet
							? `Libre ${formatNumber(data.wallet.free_value, 2)} · en órdenes ${formatNumber(data.wallet.locked_value, 2)}`
							: 'Aún sin sincronizar'
					}
					icon={<IconWallet className="size-4" />}
					isLoading={overviewQuery.isLoading}
				/>
				<StatCard
					label="En agentes"
					value={money(data?.agents_capital)}
					hint={`${data?.agents.length ?? 0} agentes del fondo`}
					icon={<IconRobot className="size-4" />}
					isLoading={overviewQuery.isLoading}
				/>
				<StatCard
					label="Retiros por pagar"
					value={money(data?.open_withdrawals_total)}
					hint={
						<Link
							to="/admin/withdrawals"
							className="underline-offset-4 hover:underline"
						>
							{data?.open_withdrawals_count ?? 0} pendientes
						</Link>
					}
					icon={<IconArrowUpFromArc className="size-4" />}
					isLoading={overviewQuery.isLoading}
				/>
				<StatCard
					label="Depósitos por resolver"
					value={money(data?.deposits_waiting_total)}
					hint={
						<Link
							to="/admin/deposits"
							className="underline-offset-4 hover:underline"
						>
							{data?.deposits_waiting_count ?? 0} esperando al exchange o en
							revisión
						</Link>
					}
					icon={<IconArrowDownToArc className="size-4" />}
					isLoading={overviewQuery.isLoading}
				/>
			</div>

			<div className="grid gap-6 lg:grid-cols-2">
				<Card>
					<CardHeader>
						<CardTitle>Conciliación</CardTitle>
						<CardDescription>
							Lo que hay en la billetera menos lo que tiene dueño en el fondo.
							{data?.wallet?.ts
								? ` Billetera al ${formatDateTime(data.wallet.ts)}.`
								: ''}
						</CardDescription>
					</CardHeader>
					<CardContent className="flex flex-col gap-2">
						{overviewQuery.isLoading || !data ? (
							<Skeleton className="h-40 w-full" />
						) : (
							<>
								<Line
									label="Billetera (a precio de mercado)"
									value={money(data.wallet?.total_value)}
								/>
								<Line
									label="− Capital de los agentes (lo abierto a costo)"
									value={money(data.agents_capital)}
								/>
								<Line
									label="− Pendiente de asignar de las personas"
									value={money(data.pending_total)}
								/>
								<Line
									label="− Disponible de las personas"
									value={money(data.available_total)}
								/>
								<Line
									label="Diferencia"
									value={money(data.difference)}
									strong
									className={cn(
										difference !== null &&
											!balanced &&
											(difference < 0 ? 'text-destructive' : 'text-chart-1'),
									)}
								/>
								{data.difference === null ? (
									<Alert>
										<IconClockHour4 />
										<AlertTitle>Sin datos de la billetera</AlertTitle>
										<AlertDescription>
											Sincroniza la billetera para poder conciliar.
										</AlertDescription>
									</Alert>
								) : balanced ? (
									<Alert>
										<IconCircleCheck />
										<AlertTitle>Todo cuadra</AlertTitle>
										<AlertDescription>
											Cada peso de la billetera tiene dueño en el fondo.
										</AlertDescription>
									</Alert>
								) : difference !== null && difference > 0 ? (
									<Alert>
										<IconCoins />
										<AlertTitle>
											Hay más en la billetera que en el fondo
										</AlertTitle>
										<AlertDescription>
											Suele ser dinero que llegó y aún no se acredita (depósitos
											por resolver o sin reclamar) o posiciones abiertas que hoy
											valen más que su costo. Se ajusta solo al liquidar.
										</AlertDescription>
									</Alert>
								) : (
									<Alert variant="destructive">
										<IconAlertTriangle />
										<AlertTitle>Falta dinero en la billetera</AlertTitle>
										<AlertDescription>
											Puede ser una posición abierta que hoy vale menos que su
											costo, comisiones pagadas en otra moneda o dinero que
											salió de la billetera por fuera del fondo. Revísalo antes
											de pagar retiros.
										</AlertDescription>
									</Alert>
								)}
								{data.wallet && data.wallet.missing_prices.length > 0 && (
									<p className="text-xs text-muted-foreground">
										Sin precio (no suman al total):{' '}
										{data.wallet.missing_prices.join(', ')}.
									</p>
								)}
								{data.last_sync_error && (
									<p className="text-xs text-destructive">
										La última sincronización falló; el total puede estar
										desactualizado.
									</p>
								)}
							</>
						)}
					</CardContent>
				</Card>

				<Card>
					<CardHeader>
						<CardTitle>Saldos de las personas</CardTitle>
						<CardDescription>
							El dinero que aún no está en un agente.
						</CardDescription>
					</CardHeader>
					<CardContent className="flex flex-col gap-2">
						{overviewQuery.isLoading || !data ? (
							<Skeleton className="h-28 w-full" />
						) : (
							<>
								<Line
									label="Pendiente de asignar"
									value={money(data.pending_total)}
								/>
								<Line label="Disponible" value={money(data.available_total)} />
								<Line
									label="De eso, reservado en retiros por pagar"
									value={money(data.open_withdrawals_total)}
									className="pl-4"
								/>
								<Line
									label="En cola para entrar a un agente"
									value={money(data.queued_allocations)}
								/>
								<p className="pt-2 text-xs text-muted-foreground">
									Detalle por persona en{' '}
									<Link
										to="/admin/participants"
										className="underline underline-offset-4"
									>
										Participantes
									</Link>
									.
								</p>
							</>
						)}
					</CardContent>
				</Card>
			</div>

			<section className="flex flex-col gap-3">
				<h2 className="text-base font-semibold">Capital por agente</h2>
				<DataTable
					columns={agentColumns}
					rows={data?.agents}
					getRowId={(row) => row.id}
					isLoading={overviewQuery.isLoading}
					empty="Aún no hay agentes en el fondo."
				/>
			</section>

			<section className="flex flex-col gap-3">
				<h2 className="text-base font-semibold">
					Ganancias de propietarios y socios
				</h2>
				<p className="text-sm text-muted-foreground">
					Comisiones recibidas más la ganancia de su propio dinero en los
					agentes (neta de la comisión que pagaron). Lo de los agentes vale lo
					de su última liquidación.
				</p>
				<DataTable
					columns={ownerColumns}
					rows={data?.owners}
					getRowId={(row) => row.user_id}
					isLoading={overviewQuery.isLoading}
					empty="Aún no hay propietarios ni socios activos."
				/>
			</section>
		</div>
	);
}
