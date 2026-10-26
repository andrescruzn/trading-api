import {
	IconArrowDownToArc,
	IconArrowUpFromArc,
	IconClockHour4,
	IconCoins,
	IconFileSpreadsheet,
	IconLoader2,
	IconPlus,
	IconRobot,
	IconWallet,
} from '@tabler/icons-react';
import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type {
	DepositRequest,
	Participation,
	RedemptionRequest,
} from '@/modules/fund/api/fund.api';
import { listAllMyLedger } from '@/modules/fund/api/fund-overview.api';
import type { Withdrawal } from '@/modules/fund/api/fund-payouts.api';
import { CancelDepositDialog } from '@/modules/fund/components/deposit-decision-dialogs';
import { DepositFormDialog } from '@/modules/fund/components/deposit-form-dialog';
import { DepositInstructions } from '@/modules/fund/components/deposit-instructions';
import { DepositRequestsTable } from '@/modules/fund/components/deposit-requests-table';
import { FeeScheduleTiers } from '@/modules/fund/components/fee-tables';
import { LedgerTable } from '@/modules/fund/components/ledger-table';
import { ParticipationsTable } from '@/modules/fund/components/participations-table';
import { PayoutMethodDialog } from '@/modules/fund/components/payout-method-dialog';
import { PayoutMethodsTable } from '@/modules/fund/components/payout-methods-table';
import { RedemptionDialog } from '@/modules/fund/components/redemption-dialog';
import {
	RedemptionLinesTable,
	RedemptionRequestsTable,
} from '@/modules/fund/components/redemptions-tables';
import { CancelWithdrawalDialog } from '@/modules/fund/components/withdrawal-decision-dialogs';
import { WithdrawalDialog } from '@/modules/fund/components/withdrawal-dialog';
import { WithdrawalsTable } from '@/modules/fund/components/withdrawals-table';
import { useMySummaryQuery } from '@/modules/fund/hooks/use-fund-overview-queries';
import { useCancelRedemptionMutation } from '@/modules/fund/hooks/use-fund-payouts-mutations';
import {
	useFeeScheduleQuery,
	useMyPayoutMethodsQuery,
	useMyRedemptionsQuery,
	useMyWithdrawableQuery,
	useWithdrawalsQuery,
} from '@/modules/fund/hooks/use-fund-payouts-queries';
import { useMyParticipationsQuery } from '@/modules/fund/hooks/use-fund-pools-queries';
import {
	useDepositInfoQuery,
	useDepositsQuery,
	useLedgerQuery,
	useMyBalancesQuery,
} from '@/modules/fund/hooks/use-fund-queries';
import { downloadLedgerCsv } from '@/modules/fund/lib/fund-files';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { StatCard } from '@/modules/shared/components/stat-card';
import { useServerPagination } from '@/modules/shared/hooks/use-server-pagination';
import {
	formatNumber,
	formatSignedPrice,
	todayInAppTimeZone,
} from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { Skeleton } from '@/modules/ui/components/skeleton';
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from '@/modules/ui/components/tabs';
import { toast } from '@/modules/ui/components/toast';
import { cn } from '@/modules/ui/lib/utils';

const NO_FILTERS = {};

function Earning({
	label,
	value,
	hint,
	strong,
}: {
	label: string;
	value: number;
	hint?: string;
	strong?: boolean;
}) {
	return (
		<div className="flex flex-col gap-1">
			<span className="text-sm text-muted-foreground">{label}</span>
			<span
				className={cn(
					'tabular-nums',
					strong ? 'text-2xl font-semibold' : 'text-lg font-medium',
					value >= 0 ? 'text-chart-1' : 'text-destructive',
				)}
			>
				{formatSignedPrice(value)} USDT
			</span>
			{hint && <span className="text-xs text-muted-foreground">{hint}</span>}
		</div>
	);
}

function Section({
	title,
	action,
	children,
}: {
	title: string;
	action?: React.ReactNode;
	children: React.ReactNode;
}) {
	return (
		<section className="flex flex-col gap-3">
			<div className="flex items-center justify-between gap-4">
				<h2 className="text-base font-semibold">{title}</h2>
				{action}
			</div>
			{children}
		</section>
	);
}

/**
 * Mi saldo en el fondo común (todos los roles): saldos, depositar, sacar
 * dinero de los agentes, retirar y la comisión. Nunca muestra el saldo
 * total de la billetera.
 */
export function MyFundPage() {
	usePageBreadcrumb([{ label: 'Mi inversión' }, { label: 'Mi saldo' }]);
	const balancesQuery = useMyBalancesQuery();
	const infoQuery = useDepositInfoQuery();
	const deposits = useServerPagination('my-deposits');
	const depositsQuery = useDepositsQuery(NO_FILTERS, deposits.params);
	const ledger = useServerPagination('my-ledger');
	const ledgerQuery = useLedgerQuery(null, ledger.params);
	const withdrawals = useServerPagination('my-withdrawals');
	const withdrawalsQuery = useWithdrawalsQuery(NO_FILTERS, withdrawals.params);
	const participationsQuery = useMyParticipationsQuery();
	const redemptionsQuery = useMyRedemptionsQuery();
	const withdrawableQuery = useMyWithdrawableQuery();
	const methodsQuery = useMyPayoutMethodsQuery();
	const feeQuery = useFeeScheduleQuery();
	const summaryQuery = useMySummaryQuery();
	const cancelRedemptionMutation = useCancelRedemptionMutation();
	const exportMutation = useMutation({ mutationFn: listAllMyLedger });

	const [registering, setRegistering] = useState(false);
	const [canceling, setCanceling] = useState<DepositRequest | null>(null);
	const [redeeming, setRedeeming] = useState<Participation | null>(null);
	const [withdrawing, setWithdrawing] = useState(false);
	const [addingMethod, setAddingMethod] = useState(false);
	const [cancelingWithdrawal, setCancelingWithdrawal] =
		useState<Withdrawal | null>(null);

	const balances = balancesQuery.data;
	const info = infoQuery.data;
	const asset = info?.asset ?? 'USDT';
	// Lo invertido vale lo de la última liquidación de cada agente
	const inAgents = (participationsQuery.data ?? []).reduce(
		(total, participation) => total + Number(participation.value),
		0,
	);
	const withdrawable = withdrawableQuery.data?.withdrawable;
	const reserved =
		balances && withdrawable !== undefined
			? Number(balances.available) - Number(withdrawable)
			: 0;
	const activeMethods = (methodsQuery.data ?? []).filter(
		(method) => method.is_active,
	);
	const redemptions = redemptionsQuery.data;
	const summary = summaryQuery.data;

	function exportLedger() {
		exportMutation.mutate(undefined, {
			onSuccess: (entries) =>
				downloadLedgerCsv(
					entries,
					`extracto-fondo-${todayInAppTimeZone()}.csv`,
				),
			onError: (error) =>
				toast.add({
					title: 'No pudimos armar el extracto',
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

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Mi saldo"
				description="Tu dinero en el fondo: lo que depositaste, lo que está en los agentes, lo que puedes retirar y cada movimiento."
				actions={[
					{
						label: 'Retirar',
						icon: <IconArrowUpFromArc />,
						variant: 'outline',
						onClick: () => setWithdrawing(true),
						disabled: !withdrawable || Number(withdrawable) <= 0,
					},
					{
						label: 'Registrar depósito',
						icon: <IconArrowDownToArc />,
						onClick: () => setRegistering(true),
						disabled: !info?.enabled,
					},
				]}
			/>

			{balancesQuery.error && (
				<ErrorAlert
					title="No pudimos cargar tu saldo"
					error={balancesQuery.error}
				/>
			)}

			<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<StatCard
					label="Pendiente de asignar"
					value={
						balances ? `${formatNumber(balances.pending, 2)} ${asset}` : '—'
					}
					hint="Depósitos confirmados que aún no están en un agente"
					icon={<IconClockHour4 className="size-4" />}
					isLoading={balancesQuery.isLoading}
				/>
				<StatCard
					label="Disponible"
					value={
						balances ? `${formatNumber(balances.available, 2)} ${asset}` : '—'
					}
					hint={
						reserved > 0
							? `${formatNumber(reserved, 2)} ${asset} reservados en retiros por enviar`
							: 'Lo que ya pasó por un agente y puedes retirar'
					}
					icon={<IconCoins className="size-4" />}
					isLoading={balancesQuery.isLoading}
				/>
				<StatCard
					label="En agentes"
					value={`${formatNumber(inAgents, 2)} ${asset}`}
					hint="Lo que vale tu dinero en los agentes a su última liquidación"
					icon={<IconRobot className="size-4" />}
					isLoading={participationsQuery.isLoading}
				/>
				<StatCard
					label="Total"
					value={
						balances
							? `${formatNumber(Number(balances.total) + inAgents, 2)} ${asset}`
							: '—'
					}
					hint="Pendiente + disponible + en agentes"
					icon={<IconWallet className="size-4" />}
					isLoading={balancesQuery.isLoading || participationsQuery.isLoading}
				/>
			</div>

			{summary && (
				<Card>
					<CardHeader>
						<CardTitle>Lo que has ganado</CardTitle>
						<CardDescription>
							Lo de los agentes vale lo de su última liquidación; entre
							liquidaciones el agente puede ir ganando o perdiendo.
						</CardDescription>
					</CardHeader>
					<CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
						<Earning
							label="Ya salió de los agentes"
							value={Number(summary.realized_gain) - Number(summary.fees_paid)}
							hint={`Después de ${formatNumber(summary.fees_paid, 2)} ${asset} de comisión`}
						/>
						<Earning
							label="En los agentes (aún no sale)"
							value={Number(summary.unrealized_gain)}
							hint={`Aportaste ${formatNumber(summary.in_agents_cost, 2)} · vale ${formatNumber(summary.in_agents_value, 2)}`}
						/>
						{Number(summary.commissions) > 0 && (
							<Earning
								label="Comisiones recibidas"
								value={Number(summary.commissions)}
								hint="Tu parte de las comisiones del fondo"
							/>
						)}
						<Earning
							label="Total"
							value={Number(summary.total_earned)}
							strong
						/>
					</CardContent>
				</Card>
			)}

			{info && !info.enabled && (
				<Alert>
					<IconClockHour4 />
					<AlertTitle>Aún no se puede depositar</AlertTitle>
					<AlertDescription>
						Los super admin todavía no configuran la billetera o sus redes de
						depósito.
					</AlertDescription>
				</Alert>
			)}
			{info?.enabled && <DepositInstructions info={info} />}

			<Tabs defaultValue="agents">
				<TabsList className="flex-wrap">
					<TabsTrigger value="agents">Mis agentes</TabsTrigger>
					<TabsTrigger value="withdrawals">Retiros</TabsTrigger>
					<TabsTrigger value="commission">Comisión</TabsTrigger>
					<TabsTrigger value="deposits">Mis depósitos</TabsTrigger>
					<TabsTrigger value="ledger">Movimientos</TabsTrigger>
				</TabsList>

				<TabsContent value="agents" className="flex flex-col gap-6 pt-2">
					<ParticipationsTable
						rows={participationsQuery.data}
						isLoading={participationsQuery.isLoading}
						error={participationsQuery.error}
						onRedeem={setRedeeming}
					/>
					<Section title="Salidas en cola">
						<RedemptionRequestsTable
							rows={redemptions?.queued}
							isLoading={redemptionsQuery.isLoading}
							error={redemptionsQuery.error}
							agents={redemptions?.agents}
							empty="No tienes salidas pendientes. Usa «Sacar dinero» en un agente."
							onCancel={cancelRedemption}
							isCanceling={cancelRedemptionMutation.isPending}
						/>
					</Section>
					<Section title="Lo que salió de tus agentes">
						<RedemptionLinesTable
							rows={redemptions?.lines}
							isLoading={redemptionsQuery.isLoading}
							error={redemptionsQuery.error}
							agents={redemptions?.agents}
						/>
					</Section>
				</TabsContent>

				<TabsContent value="withdrawals" className="flex flex-col gap-6 pt-2">
					<WithdrawalsTable
						rows={withdrawalsQuery.data?.items}
						isLoading={withdrawalsQuery.isLoading}
						isFetching={withdrawalsQuery.isPlaceholderData}
						error={withdrawalsQuery.error}
						empty="Aún no pides retiros."
						pagination={withdrawals.tablePagination(withdrawalsQuery.data)}
						onCancel={setCancelingWithdrawal}
					/>
					<Section
						title="Direcciones de retiro"
						action={
							<Button variant="outline" onClick={() => setAddingMethod(true)}>
								<IconPlus />
								Agregar dirección
							</Button>
						}
					>
						<PayoutMethodsTable
							rows={activeMethods}
							isLoading={methodsQuery.isLoading}
							error={methodsQuery.error}
						/>
					</Section>
				</TabsContent>

				<TabsContent value="commission" className="flex flex-col gap-6 pt-2">
					<Card>
						<CardHeader>
							<CardTitle>Tabla de comisión vigente</CardTitle>
							<CardDescription>
								Se cobra solo sobre la ganancia del dinero que sale de un
								agente, en la liquidación.
							</CardDescription>
						</CardHeader>
						<CardContent>
							{feeQuery.isLoading ? (
								<Skeleton className="h-20 w-full" />
							) : feeQuery.error ? (
								<ErrorAlert
									title="No pudimos cargar la tabla de comisión"
									error={feeQuery.error}
								/>
							) : feeQuery.data ? (
								<FeeScheduleTiers schedule={feeQuery.data} />
							) : (
								<span className="text-sm text-muted-foreground">
									Los super admin aún no publican la tabla de comisión.
								</span>
							)}
						</CardContent>
					</Card>
				</TabsContent>

				<TabsContent value="deposits" className="pt-2">
					<DepositRequestsTable
						rows={depositsQuery.data?.items}
						isLoading={depositsQuery.isLoading}
						isFetching={depositsQuery.isPlaceholderData}
						error={depositsQuery.error}
						empty="Aún no registras depósitos."
						pagination={deposits.tablePagination(depositsQuery.data)}
						onCancel={setCanceling}
					/>
				</TabsContent>
				<TabsContent value="ledger" className="flex flex-col gap-3 pt-2">
					<Button
						variant="outline"
						className="self-end"
						onClick={exportLedger}
						disabled={exportMutation.isPending}
					>
						{exportMutation.isPending ? (
							<IconLoader2 className="animate-spin" />
						) : (
							<IconFileSpreadsheet />
						)}
						Descargar extracto (CSV)
					</Button>
					<LedgerTable
						rows={ledgerQuery.data?.items}
						isLoading={ledgerQuery.isLoading}
						isFetching={ledgerQuery.isPlaceholderData}
						error={ledgerQuery.error}
						pagination={ledger.tablePagination(ledgerQuery.data)}
					/>
				</TabsContent>
			</Tabs>

			{info?.enabled && (
				<DepositFormDialog
					open={registering}
					onOpenChange={setRegistering}
					info={info}
				/>
			)}
			<CancelDepositDialog
				request={canceling}
				onClose={() => setCanceling(null)}
			/>
			<RedemptionDialog
				participation={redeeming}
				minHoldDays={info?.min_hold_days ?? 30}
				onClose={() => setRedeeming(null)}
			/>
			<WithdrawalDialog open={withdrawing} onOpenChange={setWithdrawing} />
			<PayoutMethodDialog open={addingMethod} onOpenChange={setAddingMethod} />
			<CancelWithdrawalDialog
				withdrawal={cancelingWithdrawal}
				onClose={() => setCancelingWithdrawal(null)}
			/>
		</div>
	);
}
