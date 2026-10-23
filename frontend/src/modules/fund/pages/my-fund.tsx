import {
	IconArrowDownToArc,
	IconClockHour4,
	IconCoins,
	IconRobot,
	IconWallet,
} from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { DepositRequest } from '@/modules/fund/api/fund.api';
import { CancelDepositDialog } from '@/modules/fund/components/deposit-decision-dialogs';
import { DepositFormDialog } from '@/modules/fund/components/deposit-form-dialog';
import { DepositInstructions } from '@/modules/fund/components/deposit-instructions';
import { DepositRequestsTable } from '@/modules/fund/components/deposit-requests-table';
import { LedgerTable } from '@/modules/fund/components/ledger-table';
import { ParticipationsTable } from '@/modules/fund/components/participations-table';
import { useMyParticipationsQuery } from '@/modules/fund/hooks/use-fund-pools-queries';
import {
	useDepositInfoQuery,
	useDepositsQuery,
	useLedgerQuery,
	useMyBalancesQuery,
} from '@/modules/fund/hooks/use-fund-queries';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { StatCard } from '@/modules/shared/components/stat-card';
import { useServerPagination } from '@/modules/shared/hooks/use-server-pagination';
import { formatNumber } from '@/modules/shared/lib/format';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from '@/modules/ui/components/tabs';

const NO_FILTERS = {};

/**
 * Mi saldo en el fondo común (todos los roles): saldos, cómo depositar, mis
 * depósitos y mis movimientos. Nunca muestra el saldo total de la billetera.
 */
export function MyFundPage() {
	usePageBreadcrumb([{ label: 'Mi inversión' }, { label: 'Mi saldo' }]);
	const balancesQuery = useMyBalancesQuery();
	const infoQuery = useDepositInfoQuery();
	const deposits = useServerPagination('my-deposits');
	const depositsQuery = useDepositsQuery(NO_FILTERS, deposits.params);
	const ledger = useServerPagination('my-ledger');
	const ledgerQuery = useLedgerQuery(null, ledger.params);
	const participationsQuery = useMyParticipationsQuery();
	const [registering, setRegistering] = useState(false);
	const [canceling, setCanceling] = useState<DepositRequest | null>(null);

	const balances = balancesQuery.data;
	const info = infoQuery.data;
	const asset = info?.asset ?? 'USDT';
	// Lo invertido vale lo de la última liquidación de cada agente
	const inAgents = (participationsQuery.data ?? []).reduce(
		(total, participation) => total + Number(participation.value),
		0,
	);

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Mi saldo"
				description="Tu dinero en el fondo: lo que depositaste, lo que está listo para invertir y cada movimiento."
				actions={[
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
					hint="Lo que ya pasó por un agente y puedes retirar"
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
				<TabsList>
					<TabsTrigger value="agents">Mis agentes</TabsTrigger>
					<TabsTrigger value="deposits">Mis depósitos</TabsTrigger>
					<TabsTrigger value="ledger">Movimientos</TabsTrigger>
				</TabsList>
				<TabsContent value="agents" className="pt-2">
					<ParticipationsTable
						rows={participationsQuery.data}
						isLoading={participationsQuery.isLoading}
						error={participationsQuery.error}
					/>
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
				<TabsContent value="ledger" className="pt-2">
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
		</div>
	);
}
