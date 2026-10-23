import { IconRefresh, IconUserPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import { useOwners } from '@/modules/auth/hooks/use-users-queries';
import type {
	DepositRequest,
	DepositStatus,
	ExchangeDeposit,
} from '@/modules/fund/api/fund.api';
import { AssignUnclaimedDialog } from '@/modules/fund/components/assign-unclaimed-dialog';
import { CopyText } from '@/modules/fund/components/copy-text';
import {
	ConfirmDepositDialog,
	RejectDepositDialog,
} from '@/modules/fund/components/deposit-decision-dialogs';
import { DepositRequestsTable } from '@/modules/fund/components/deposit-requests-table';
import { useVerifyDepositsMutation } from '@/modules/fund/hooks/use-fund-mutations';
import {
	useDepositsQuery,
	useUnclaimedDepositsQuery,
} from '@/modules/fund/hooks/use-fund-queries';
import { DEPOSIT_STATUS_OPTIONS } from '@/modules/fund/lib/fund-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { useServerPagination } from '@/modules/shared/hooks/use-server-pagination';
import { formatDateTime, formatNumber } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button } from '@/modules/ui/components/button';
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from '@/modules/ui/components/tabs';
import { toast } from '@/modules/ui/components/toast';

const ALL = 'all';

const STATUS_FILTER_OPTIONS = [
	{ value: ALL, label: 'Todos los estados' },
	...DEPOSIT_STATUS_OPTIONS,
];

/** Depósitos al fondo (staff): solicitudes por resolver y depósitos sin reclamar. */
export function AdminDepositsPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Depósitos' }]);
	const canManage = useCanManage();
	const owners = useOwners(ALL);
	const [status, setStatus] = useState<string>('review');
	const [owner, setOwner] = useState(ALL);
	const [tab, setTab] = useState('requests');
	const [confirming, setConfirming] = useState<DepositRequest | null>(null);
	const [rejecting, setRejecting] = useState<DepositRequest | null>(null);
	const [assigning, setAssigning] = useState<ExchangeDeposit | null>(null);
	const verifyMutation = useVerifyDepositsMutation();

	const filters = {
		status: status === ALL ? undefined : (status as DepositStatus),
		user_id: owner === ALL ? undefined : Number(owner),
	};
	const { params, tablePagination } = useServerPagination(
		JSON.stringify(filters),
	);
	const depositsQuery = useDepositsQuery(filters, params);
	const unclaimedQuery = useUnclaimedDepositsQuery(tab === 'unclaimed');

	function verify() {
		verifyMutation.mutate(undefined, {
			onSuccess: (s) =>
				toast.add({
					title: 'Verificación terminada',
					description: `Revisados: ${s.checked} · confirmados: ${s.confirmed} · a revisión: ${s.review} · vencidos: ${s.expired} · esperando: ${s.waiting}.`,
					type: 'success',
				}),
			onError: (error) =>
				toast.add({
					title: 'No pudimos verificar los depósitos',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	const unclaimedColumns: DataTableColumn<ExchangeDeposit>[] = [
		{
			id: 'ts',
			header: 'Llegó',
			className: 'whitespace-nowrap',
			cell: (row) => formatDateTime(row.ts),
		},
		{
			id: 'network',
			header: 'Red',
			cell: (row) => <span className="font-mono">{row.network ?? '—'}</span>,
		},
		{
			id: 'txid',
			header: 'Txid',
			className: 'max-w-48',
			cell: (row) => <CopyText value={row.txid} label="Txid" truncate />,
		},
		{
			id: 'from',
			header: 'Desde',
			className: 'max-w-48',
			cell: (row) =>
				row.address_from ? (
					<CopyText value={row.address_from} label="Dirección" truncate />
				) : (
					<span className="text-muted-foreground">—</span>
				),
		},
		{
			id: 'amount',
			header: 'Monto',
			className: 'text-right tabular-nums font-medium',
			cell: (row) => `${formatNumber(row.amount)} ${row.asset}`,
		},
		...(canManage
			? [
					{
						id: 'actions',
						header: <span className="sr-only">Acciones</span>,
						className: 'text-right',
						cell: (row: ExchangeDeposit) => (
							<Button
								variant="ghost"
								size="sm"
								onClick={() => setAssigning(row)}
							>
								<IconUserPlus />
								Asignar
							</Button>
						),
					},
				]
			: []),
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Depósitos"
				description="Lo que la gente envía a la billetera. Los que coinciden con el exchange se confirman solos; aquí se resuelven los que esperan una decisión."
				actions={[
					{
						label: verifyMutation.isPending
							? 'Verificando…'
							: 'Verificar ahora',
						icon: <IconRefresh />,
						onClick: verify,
						disabled: verifyMutation.isPending,
						hidden: !canManage,
					},
				]}
			/>
			<Tabs value={tab} onValueChange={(value) => setTab(String(value))}>
				<TabsList>
					<TabsTrigger value="requests">Solicitudes</TabsTrigger>
					<TabsTrigger value="unclaimed">Sin reclamar</TabsTrigger>
				</TabsList>
				<TabsContent value="requests" className="flex flex-col gap-3 pt-2">
					<div className="grid gap-3 sm:grid-cols-2 lg:max-w-2xl">
						<OptionSelect
							aria-label="Estado"
							size="sm"
							value={status}
							onChange={(value) => setStatus(value ?? ALL)}
							options={STATUS_FILTER_OPTIONS}
						/>
						<OptionSelect
							aria-label="Persona"
							size="sm"
							value={owner}
							onChange={(value) => setOwner(value ?? ALL)}
							options={owners.options}
						/>
					</div>
					<DepositRequestsTable
						rows={depositsQuery.data?.items}
						isLoading={depositsQuery.isLoading}
						isFetching={depositsQuery.isPlaceholderData}
						error={depositsQuery.error}
						empty={
							status === 'review'
								? 'No hay depósitos esperando una decisión.'
								: 'No hay depósitos con esos filtros.'
						}
						pagination={tablePagination(depositsQuery.data)}
						renderOwner={(row) => (
							<OwnerCell userId={row.user_id} users={owners.byId} />
						)}
						onConfirm={canManage ? setConfirming : undefined}
						onReject={canManage ? setRejecting : undefined}
					/>
				</TabsContent>
				<TabsContent value="unclaimed" className="flex flex-col gap-3 pt-2">
					<p className="text-sm text-muted-foreground">
						Depósitos de los últimos 30 días que entraron a la billetera sin que
						nadie los registrara. Explican una diferencia en la conciliación.
					</p>
					<DataTable
						columns={unclaimedColumns}
						rows={unclaimedQuery.data}
						getRowId={(row) => row.txid}
						isLoading={unclaimedQuery.isLoading}
						error={unclaimedQuery.error}
						errorTitle="No pudimos leer los depósitos del exchange"
						empty="No hay depósitos sin reclamar."
					/>
				</TabsContent>
			</Tabs>

			<ConfirmDepositDialog
				request={confirming}
				onClose={() => setConfirming(null)}
			/>
			<RejectDepositDialog
				request={rejecting}
				onClose={() => setRejecting(null)}
			/>
			<AssignUnclaimedDialog
				deposit={assigning}
				onClose={() => setAssigning(null)}
			/>
		</div>
	);
}
