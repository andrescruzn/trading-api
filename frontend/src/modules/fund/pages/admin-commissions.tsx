import { IconPencil } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { UserSummary } from '@/modules/auth/api/users.api';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import { useOwners } from '@/modules/auth/hooks/use-users-queries';
import { ROLES, STAFF_ROLES } from '@/modules/auth/lib/roles';
import type {
	CommissionShares,
	OwnerEarning,
} from '@/modules/fund/api/fund-payouts.api';
import { CommissionSharesDialog } from '@/modules/fund/components/commission-shares-dialog';
import { FeeScheduleDialog } from '@/modules/fund/components/fee-schedule-dialog';
import { FeeScheduleTiers } from '@/modules/fund/components/fee-tables';
import {
	useCommissionSharesQuery,
	useFeeScheduleQuery,
	useOwnerEarningsQuery,
} from '@/modules/fund/hooks/use-fund-payouts-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import {
	formatDateTime,
	formatNumber,
	formatPercentValue,
} from '@/modules/shared/lib/format';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardAction,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { Skeleton } from '@/modules/ui/components/skeleton';

const ALL = 'all';

type ShareRow = { user_id: number; pct: string };

function sharesTotal(shares: CommissionShares | null | undefined) {
	return (shares?.shares ?? []).reduce((sum, s) => sum + Number(s.pct), 0);
}

/**
 * Comisión del fondo (staff): la tabla escalonada que pagan los
 * participantes, cómo se reparte entre propietarios y socios, y cuánto ha
 * recibido cada uno. Solo un super admin la cambia; cada cambio es una
 * versión nueva.
 */
export function AdminCommissionsPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Comisiones' }]);
	const canManage = useCanManage();
	const owners = useOwners(ALL);
	const feeQuery = useFeeScheduleQuery();
	const sharesQuery = useCommissionSharesQuery();
	const earningsQuery = useOwnerEarningsQuery();
	const [editingFees, setEditingFees] = useState(false);
	const [editingShares, setEditingShares] = useState(false);

	const current = sharesQuery.data?.current ?? null;
	// Pueden recibir comisión: super admin y socios activos
	const staff: UserSummary[] = (owners.usersQuery.data ?? [])
		.filter(
			(user) =>
				user.status === 'active' &&
				!!user.role_code &&
				STAFF_ROLES.includes(user.role_code),
		)
		.sort((a, b) =>
			a.role_code === b.role_code
				? a.id - b.id
				: a.role_code === ROLES.SUPER_ADMIN
					? -1
					: 1,
		);

	const shareColumns: DataTableColumn<ShareRow>[] = [
		{
			id: 'user',
			header: 'Persona',
			cell: (row) => <OwnerCell userId={row.user_id} users={owners.byId} />,
		},
		{
			id: 'pct',
			header: 'Recibe',
			className: 'text-right tabular-nums font-medium',
			cell: (row) => formatPercentValue(row.pct),
		},
	];

	const earningColumns: DataTableColumn<OwnerEarning>[] = [
		{
			id: 'user',
			header: 'Persona',
			cell: (row) => <OwnerCell userId={row.user_id} users={owners.byId} />,
		},
		{
			id: 'commissions',
			header: 'Comisiones recibidas',
			className: 'text-right tabular-nums font-medium',
			cell: (row) => `${formatNumber(row.commissions, 2)} USDT`,
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Comisiones"
				description="La comisión se cobra solo sobre la ganancia del dinero que sale de un agente, en su liquidación, y se reparte entre propietarios y socios."
			/>

			<div className="grid gap-6 lg:grid-cols-2">
				<Card>
					<CardHeader>
						<CardTitle>Tabla de comisión</CardTitle>
						<CardDescription>
							La ven todos los participantes. Las liquidaciones ya hechas
							guardan la tabla con la que se cobraron.
						</CardDescription>
						{canManage && (
							<CardAction>
								<Button variant="outline" onClick={() => setEditingFees(true)}>
									<IconPencil />
									{feeQuery.data ? 'Cambiar' : 'Publicar'}
								</Button>
							</CardAction>
						)}
					</CardHeader>
					<CardContent>
						{feeQuery.isLoading ? (
							<Skeleton className="h-24 w-full" />
						) : feeQuery.error ? (
							<ErrorAlert
								title="No pudimos cargar la tabla de comisión"
								error={feeQuery.error}
							/>
						) : feeQuery.data ? (
							<FeeScheduleTiers schedule={feeQuery.data} />
						) : (
							<span className="text-sm text-muted-foreground">
								Aún no hay tabla. Sin ella no se puede liquidar un agente con
								salidas pedidas.
							</span>
						)}
					</CardContent>
				</Card>

				<Card>
					<CardHeader>
						<CardTitle>Reparto entre propietarios y socios</CardTitle>
						<CardDescription>
							{current
								? `Vigente desde el ${formatDateTime(current.created_at)}${
										current.note ? ` · ${current.note}` : ''
									}`
								: 'Aún no hay reparto. Sin él no se puede liquidar un agente con salidas pedidas.'}
						</CardDescription>
						{canManage && (
							<CardAction>
								<Button
									variant="outline"
									onClick={() => setEditingShares(true)}
									disabled={staff.length === 0}
								>
									<IconPencil />
									{current ? 'Cambiar' : 'Definir'}
								</Button>
							</CardAction>
						)}
					</CardHeader>
					<CardContent>
						{sharesQuery.error ? (
							<ErrorAlert
								title="No pudimos cargar el reparto"
								error={sharesQuery.error}
							/>
						) : (
							<DataTable
								columns={shareColumns}
								rows={current?.shares}
								getRowId={(row) => row.user_id}
								isLoading={sharesQuery.isLoading}
								empty="Sin reparto definido."
							/>
						)}
						{current && (
							<p className="mt-2 text-xs text-muted-foreground">
								Suma {formatPercentValue(sharesTotal(current))}. Lo que no se
								puede dividir exacto (centavos) va a quien tenga el número de
								usuario más bajo.
							</p>
						)}
					</CardContent>
				</Card>
			</div>

			<section className="flex flex-col gap-3">
				<h2 className="text-base font-semibold">Comisiones recibidas</h2>
				<DataTable
					columns={earningColumns}
					rows={earningsQuery.data}
					getRowId={(row) => row.user_id}
					isLoading={earningsQuery.isLoading}
					error={earningsQuery.error}
					errorTitle="No pudimos cargar las comisiones"
					empty="Aún no se ha cobrado comisión: llega cuando alguien saca ganancia de un agente."
				/>
			</section>

			<FeeScheduleDialog
				open={editingFees}
				onOpenChange={setEditingFees}
				current={feeQuery.data ?? null}
			/>
			<CommissionSharesDialog
				open={editingShares}
				onOpenChange={setEditingShares}
				owners={staff}
				current={current}
			/>
		</div>
	);
}
