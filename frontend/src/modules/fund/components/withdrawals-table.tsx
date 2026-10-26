import {
	IconDots,
	IconExternalLink,
	IconPaperclip,
	IconSend,
	IconX,
} from '@tabler/icons-react';
import type { UserSummary } from '@/modules/auth/api/users.api';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import type { Withdrawal } from '@/modules/fund/api/fund-payouts.api';
import { ReceiptDownloadButton } from '@/modules/fund/components/receipt-controls';
import {
	WITHDRAWAL_STATUS_BADGE_VARIANT,
	WITHDRAWAL_STATUS_LABELS,
} from '@/modules/fund/lib/fund-payouts-labels';
import {
	DataTable,
	type DataTableColumn,
	type ServerPagination,
} from '@/modules/shared/components/data-table';
import { formatDateTime, formatNumber } from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
} from '@/modules/ui/components/dropdown-menu';

type WithdrawalsTableProps = {
	rows: Withdrawal[] | undefined;
	isLoading: boolean;
	isFetching?: boolean;
	error: unknown;
	empty: string;
	pagination?: ServerPagination;
	/** Con usuarios se muestra la columna Persona (vista de staff). */
	users?: Map<number, UserSummary>;
	/** La persona anula su propio retiro mientras está por enviar. */
	onCancel?: (withdrawal: Withdrawal) => void;
	/** Super admin: registrar el envío o rechazar. */
	onPay?: (withdrawal: Withdrawal) => void;
	onReject?: (withdrawal: Withdrawal) => void;
	/** Super admin: adjuntar o cambiar el comprobante de uno enviado. */
	onAttachReceipt?: (withdrawal: Withdrawal) => void;
};

/** `9f3a2c…b81e` para que el hash no ensanche la tabla. */
function shortTxid(txid: string) {
	return txid.length <= 16 ? txid : `${txid.slice(0, 8)}…${txid.slice(-6)}`;
}

function Paid({ row }: { row: Withdrawal }) {
	if (row.status !== 'paid') return <>{row.resolution_note ?? '—'}</>;
	return (
		<div className="flex flex-col">
			{row.sent_amount !== null ? (
				<span className="tabular-nums">
					Recibió {formatNumber(row.sent_amount, 2)} USDT · comisión{' '}
					{formatNumber(row.network_fee, 2)}
				</span>
			) : (
				// Retiros viejos (pagados por banco antes del 2026-10-26)
				<span className="text-muted-foreground">Pagado por banco</span>
			)}
			{row.txid && (
				<span className="flex items-center gap-1 text-xs text-muted-foreground">
					{row.network} ·{' '}
					{row.explorer_url ? (
						<a
							href={row.explorer_url}
							target="_blank"
							rel="noreferrer"
							className="inline-flex items-center gap-0.5 font-mono underline-offset-2 hover:underline"
						>
							{shortTxid(row.txid)}
							<IconExternalLink className="size-3" />
						</a>
					) : (
						<span className="font-mono">{shortTxid(row.txid)}</span>
					)}
				</span>
			)}
			{row.resolution_note && (
				<span className="text-xs text-muted-foreground">
					{row.resolution_note}
				</span>
			)}
			{row.receipt_name && (
				<div className="-ml-2.5">
					<ReceiptDownloadButton withdrawal={row} />
				</div>
			)}
		</div>
	);
}

/** Retiros: los propios (participante) o los de todos (staff). */
export function WithdrawalsTable({
	rows,
	isLoading,
	isFetching,
	error,
	empty,
	pagination,
	users,
	onCancel,
	onPay,
	onReject,
	onAttachReceipt,
}: WithdrawalsTableProps) {
	const columns: DataTableColumn<Withdrawal>[] = [
		{
			id: 'created',
			header: 'Pedido',
			className: 'whitespace-nowrap',
			cell: (row) => formatDateTime(row.created_at),
		},
		...(users
			? [
					{
						id: 'user',
						header: 'Persona',
						cell: (row: Withdrawal) => (
							<OwnerCell userId={row.user_id} users={users} />
						),
					},
				]
			: []),
		{
			id: 'amount',
			header: 'Monto',
			className: 'text-right tabular-nums font-medium',
			cell: (row) => `${formatNumber(row.amount, 2)} USDT`,
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => (
				<Badge variant={WITHDRAWAL_STATUS_BADGE_VARIANT[row.status]}>
					{WITHDRAWAL_STATUS_LABELS[row.status]}
				</Badge>
			),
		},
		{
			id: 'paid',
			header: 'Envío',
			className: 'max-w-72',
			cell: (row) => <Paid row={row} />,
		},
		{
			id: 'resolved',
			header: 'Resuelto',
			className: 'whitespace-nowrap',
			cell: (row) => formatDateTime(row.resolved_at),
		},
	];

	if (onCancel) {
		columns.push({
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) =>
				row.status === 'requested' ? (
					<Button variant="ghost" size="sm" onClick={() => onCancel(row)}>
						<IconX />
						Anular
					</Button>
				) : null,
		});
	} else if (onPay && onReject) {
		columns.push({
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) =>
				row.status === 'requested' ? (
					<DropdownMenu>
						<DropdownMenuTrigger
							render={
								<Button
									variant="ghost"
									size="icon-sm"
									aria-label="Acciones del retiro"
								/>
							}
						>
							<IconDots />
						</DropdownMenuTrigger>
						<DropdownMenuContent align="end">
							<DropdownMenuItem onClick={() => onPay(row)}>
								<IconSend />
								Registrar envío
							</DropdownMenuItem>
							<DropdownMenuItem
								variant="destructive"
								onClick={() => onReject(row)}
							>
								<IconX />
								Rechazar
							</DropdownMenuItem>
						</DropdownMenuContent>
					</DropdownMenu>
				) : row.status === 'paid' && onAttachReceipt ? (
					<Button
						variant="ghost"
						size="sm"
						onClick={() => onAttachReceipt(row)}
					>
						<IconPaperclip />
						{row.receipt_name ? 'Cambiar comprobante' : 'Adjuntar comprobante'}
					</Button>
				) : null,
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
			errorTitle="No pudimos cargar los retiros"
			empty={empty}
			pagination={pagination}
		/>
	);
}
