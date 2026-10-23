import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import { useOwners } from '@/modules/auth/hooks/use-users-queries';
import type {
	Withdrawal,
	WithdrawalStatus,
} from '@/modules/fund/api/fund-payouts.api';
import { AttachReceiptDialog } from '@/modules/fund/components/receipt-controls';
import {
	PayWithdrawalDialog,
	RejectWithdrawalDialog,
} from '@/modules/fund/components/withdrawal-decision-dialogs';
import { WithdrawalsTable } from '@/modules/fund/components/withdrawals-table';
import { useWithdrawalsQuery } from '@/modules/fund/hooks/use-fund-payouts-queries';
import { WITHDRAWAL_STATUS_OPTIONS } from '@/modules/fund/lib/fund-payouts-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { useServerPagination } from '@/modules/shared/hooks/use-server-pagination';

const ALL = 'all';

const STATUS_FILTER_OPTIONS = [
	{ value: ALL, label: 'Todos los estados' },
	...WITHDRAWAL_STATUS_OPTIONS,
];

/** Retiros (staff): los por pagar primero; el super admin los paga o rechaza. */
export function AdminWithdrawalsPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Retiros' }]);
	const canManage = useCanManage();
	const owners = useOwners(ALL);
	const [status, setStatus] = useState<string>('requested');
	const [owner, setOwner] = useState(ALL);
	const [paying, setPaying] = useState<Withdrawal | null>(null);
	const [rejecting, setRejecting] = useState<Withdrawal | null>(null);
	const [attaching, setAttaching] = useState<Withdrawal | null>(null);

	const filters = {
		status: status === ALL ? undefined : (status as WithdrawalStatus),
		user_id: owner === ALL ? undefined : Number(owner),
	};
	const { params, tablePagination } = useServerPagination(
		JSON.stringify(filters),
	);
	const withdrawalsQuery = useWithdrawalsQuery(filters, params);

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Retiros"
				description="Lo que los participantes pidieron retirar de su saldo disponible. Se paga por fuera (banco o Nequi) y aquí se registra el pago."
			/>
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
			<WithdrawalsTable
				rows={withdrawalsQuery.data?.items}
				isLoading={withdrawalsQuery.isLoading}
				isFetching={withdrawalsQuery.isPlaceholderData}
				error={withdrawalsQuery.error}
				empty={
					status === 'requested'
						? 'No hay retiros por pagar.'
						: 'No hay retiros con esos filtros.'
				}
				pagination={tablePagination(withdrawalsQuery.data)}
				users={owners.byId}
				onPay={canManage ? setPaying : undefined}
				onReject={canManage ? setRejecting : undefined}
				onAttachReceipt={canManage ? setAttaching : undefined}
			/>
			<PayWithdrawalDialog
				withdrawal={paying}
				onClose={() => setPaying(null)}
			/>
			<RejectWithdrawalDialog
				withdrawal={rejecting}
				onClose={() => setRejecting(null)}
			/>
			<AttachReceiptDialog
				withdrawal={attaching}
				onClose={() => setAttaching(null)}
			/>
		</div>
	);
}
