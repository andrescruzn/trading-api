import {
	IconArrowBackUp,
	IconClockHour4,
	IconCoins,
	IconList,
} from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { UserSummary } from '@/modules/auth/api/users.api';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import {
	useOwners,
	userDisplayName,
} from '@/modules/auth/hooks/use-users-queries';
import type { FundBalances } from '@/modules/fund/api/fund.api';
import { LedgerTable } from '@/modules/fund/components/ledger-table';
import {
	RefundDialog,
	type RefundTarget,
} from '@/modules/fund/components/refund-dialog';
import {
	useLedgerQuery,
	useParticipantBalancesQuery,
} from '@/modules/fund/hooks/use-fund-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { StatCard } from '@/modules/shared/components/stat-card';
import { useServerPagination } from '@/modules/shared/hooks/use-server-pagination';
import { formatNumber } from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';
import {
	Sheet,
	SheetContent,
	SheetDescription,
	SheetHeader,
	SheetTitle,
} from '@/modules/ui/components/sheet';

const ALL = 'all';
const ZERO = '0';

type ParticipantRow = {
	user: UserSummary;
	balances: Pick<FundBalances, 'pending' | 'available' | 'total'>;
};

function sum(values: string[]) {
	return values.reduce((total, value) => total + Number(value), 0);
}

/** Movimientos de una persona, en un panel lateral. */
function ParticipantLedgerSheet({
	user,
	onClose,
}: {
	user: UserSummary | null;
	onClose: () => void;
}) {
	const { params, tablePagination } = useServerPagination(
		String(user?.id ?? ''),
	);
	const ledgerQuery = useLedgerQuery(user?.id ?? null, params, !!user);

	return (
		<Sheet open={!!user} onOpenChange={(open) => !open && onClose()}>
			<SheetContent className="w-full sm:max-w-3xl">
				<SheetHeader>
					<SheetTitle>
						Movimientos de {user ? userDisplayName(user) : ''}
					</SheetTitle>
					<SheetDescription>
						Cada entrada y salida de su saldo en el fondo. Nada se edita: una
						corrección es otro movimiento.
					</SheetDescription>
				</SheetHeader>
				<div className="overflow-y-auto px-4 pb-4">
					<LedgerTable
						rows={ledgerQuery.data?.items}
						isLoading={ledgerQuery.isLoading}
						isFetching={ledgerQuery.isPlaceholderData}
						error={ledgerQuery.error}
						pagination={tablePagination(ledgerQuery.data)}
					/>
				</div>
			</SheetContent>
		</Sheet>
	);
}

/** Saldo de cada persona en el fondo (staff). */
export function AdminParticipantsPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Participantes' }]);
	const canManage = useCanManage();
	const owners = useOwners(ALL);
	const balancesQuery = useParticipantBalancesQuery();
	const [viewing, setViewing] = useState<UserSummary | null>(null);
	const [refunding, setRefunding] = useState<RefundTarget | null>(null);

	const balancesById = new Map(
		(balancesQuery.data ?? []).map((balance) => [balance.user_id, balance]),
	);
	// Todas las personas con cuenta, tengan o no movimientos (inversores nuevos con 0)
	const rows: ParticipantRow[] | undefined = owners.usersQuery.data?.map(
		(user) => ({
			user,
			balances: balancesById.get(user.id) ?? {
				pending: ZERO,
				available: ZERO,
				total: ZERO,
			},
		}),
	);
	const isLoading = owners.usersQuery.isLoading || balancesQuery.isLoading;
	const balances = balancesQuery.data ?? [];

	const columns: DataTableColumn<ParticipantRow>[] = [
		{
			id: 'user',
			header: 'Persona',
			cell: (row) => <OwnerCell userId={row.user.id} users={owners.byId} />,
		},
		{
			id: 'role',
			header: 'Rol',
			cell: (row) => (
				<Badge variant="secondary">
					{row.user.role_label ?? row.user.role_code}
				</Badge>
			),
		},
		{
			id: 'pending',
			header: 'Pendiente de asignar',
			className: 'text-right tabular-nums',
			cell: (row) => formatNumber(row.balances.pending, 2),
		},
		{
			id: 'available',
			header: 'Disponible',
			className: 'text-right tabular-nums',
			cell: (row) => formatNumber(row.balances.available, 2),
		},
		{
			id: 'total',
			header: 'Total (USDT)',
			className: 'text-right tabular-nums font-medium',
			cell: (row) => formatNumber(row.balances.total, 2),
		},
		{
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) => (
				<div className="flex justify-end gap-1">
					<Button
						variant="ghost"
						size="sm"
						onClick={() => setViewing(row.user)}
					>
						<IconList />
						Movimientos
					</Button>
					{canManage && Number(row.balances.pending) > 0 && (
						<Button
							variant="ghost"
							size="sm"
							onClick={() =>
								setRefunding({
									userId: row.user.id,
									name: userDisplayName(row.user),
									pending: row.balances.pending,
								})
							}
						>
							<IconArrowBackUp />
							Devolver
						</Button>
					)}
				</div>
			),
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Participantes"
				description="Cuánto tiene cada persona en el fondo, según su libro de movimientos. Lo invertido en agentes se sumará en la siguiente fase."
			/>
			<div className="grid gap-4 sm:grid-cols-2">
				<StatCard
					label="Pendiente de asignar (todos)"
					value={`${formatNumber(sum(balances.map((b) => b.pending)), 2)} USDT`}
					hint="Depósitos confirmados que aún no están en un agente"
					icon={<IconClockHour4 className="size-4" />}
					isLoading={balancesQuery.isLoading}
				/>
				<StatCard
					label="Disponible (todos)"
					value={`${formatNumber(sum(balances.map((b) => b.available)), 2)} USDT`}
					hint="Lo que se puede retirar"
					icon={<IconCoins className="size-4" />}
					isLoading={balancesQuery.isLoading}
				/>
			</div>
			<DataTable
				columns={columns}
				rows={rows}
				getRowId={(row) => row.user.id}
				isLoading={isLoading}
				error={owners.usersQuery.error ?? balancesQuery.error}
				errorTitle="No pudimos cargar los participantes"
				empty="Aún no hay personas con cuenta."
			/>
			<ParticipantLedgerSheet user={viewing} onClose={() => setViewing(null)} />
			<RefundDialog target={refunding} onClose={() => setRefunding(null)} />
		</div>
	);
}
