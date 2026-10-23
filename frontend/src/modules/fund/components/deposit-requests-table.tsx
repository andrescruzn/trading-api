import { IconCheck, IconX } from '@tabler/icons-react';
import type { ReactNode } from 'react';
import type { DepositRequest } from '@/modules/fund/api/fund.api';
import { CopyText } from '@/modules/fund/components/copy-text';
import {
	DEPOSIT_REVIEW_REASON_LABELS,
	DEPOSIT_STATUS_BADGE_VARIANT,
	DEPOSIT_STATUS_LABELS,
} from '@/modules/fund/lib/fund-labels';
import {
	DataTable,
	type DataTableColumn,
	type ServerPagination,
} from '@/modules/shared/components/data-table';
import { formatDateTime, formatNumber } from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';

type DepositRequestsTableProps = {
	rows: DepositRequest[] | undefined;
	isLoading: boolean;
	isFetching?: boolean;
	error: unknown;
	empty: ReactNode;
	pagination: ServerPagination;
	/** Columna Persona (vistas del staff). */
	renderOwner?: (row: DepositRequest) => ReactNode;
	/** Participante: anular su solicitud pendiente. */
	onCancel?: (row: DepositRequest) => void;
	/** Super admin: resolver una solicitud abierta. */
	onConfirm?: (row: DepositRequest) => void;
	onReject?: (row: DepositRequest) => void;
};

function StatusCell({ row }: { row: DepositRequest }) {
	return (
		<div className="flex flex-col items-start gap-1">
			<Badge variant={DEPOSIT_STATUS_BADGE_VARIANT[row.status]}>
				{DEPOSIT_STATUS_LABELS[row.status]}
			</Badge>
			{row.status === 'review' && row.review_reason && (
				<span className="text-xs text-muted-foreground">
					{DEPOSIT_REVIEW_REASON_LABELS[row.review_reason]}
				</span>
			)}
			{row.resolution_note &&
				(row.status === 'rejected' || row.status === 'confirmed') && (
					<span className="text-xs text-muted-foreground">
						{row.resolution_note}
					</span>
				)}
		</div>
	);
}

/** Solicitudes de depósito (participante o staff, según las props). */
export function DepositRequestsTable({
	rows,
	isLoading,
	isFetching,
	error,
	empty,
	pagination,
	renderOwner,
	onCancel,
	onConfirm,
	onReject,
}: DepositRequestsTableProps) {
	const hasActions = !!(onCancel || onConfirm || onReject);

	const columns: DataTableColumn<DepositRequest>[] = [
		{
			id: 'created',
			header: 'Registrado',
			className: 'whitespace-nowrap',
			cell: (row) => formatDateTime(row.created_at),
		},
		...(renderOwner
			? [{ id: 'owner', header: 'Persona', cell: renderOwner }]
			: []),
		{
			id: 'network',
			header: 'Red',
			cell: (row) => <span className="font-mono">{row.network}</span>,
		},
		{
			id: 'txid',
			header: 'Txid',
			className: 'max-w-48',
			cell: (row) => <CopyText value={row.txid} label="Txid" truncate />,
		},
		{
			id: 'declared',
			header: 'Declarado',
			className: 'text-right tabular-nums',
			cell: (row) => `${formatNumber(row.declared_amount)} ${row.asset}`,
		},
		{
			id: 'credited',
			header: 'Según el exchange',
			className: 'text-right tabular-nums',
			cell: (row) =>
				row.credited_amount === null ? (
					<span className="text-muted-foreground">—</span>
				) : (
					`${formatNumber(row.credited_amount)} ${row.asset}`
				),
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => <StatusCell row={row} />,
		},
	];

	if (hasActions) {
		columns.push({
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) => {
				const open = row.status === 'pending' || row.status === 'review';
				return (
					<div className="flex justify-end gap-1">
						{onConfirm && open && (
							<Button variant="ghost" size="sm" onClick={() => onConfirm(row)}>
								<IconCheck />
								Confirmar
							</Button>
						)}
						{onReject && open && (
							<Button
								variant="ghost"
								size="sm"
								className="text-destructive"
								onClick={() => onReject(row)}
							>
								<IconX />
								Rechazar
							</Button>
						)}
						{onCancel && row.status === 'pending' && (
							<Button variant="ghost" size="sm" onClick={() => onCancel(row)}>
								<IconX />
								Anular
							</Button>
						)}
					</div>
				);
			},
		});
	}

	return (
		<DataTable
			columns={columns}
			rows={rows}
			getRowId={(row) => row.id}
			isLoading={isLoading}
			isFetching={isFetching}
			error={error}
			errorTitle="No pudimos cargar los depósitos"
			empty={empty}
			pagination={pagination}
		/>
	);
}
