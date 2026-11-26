import { IconX } from '@tabler/icons-react';
import type { UserSummary } from '@/modules/auth/api/users.api';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import type {
	FundAgentInfo,
	RedemptionRequest,
} from '@/modules/fund/api/fund.api';
import type { SettlementRedemption } from '@/modules/fund/api/fund-payouts.api';
import { FeeBreakdown } from '@/modules/fund/components/fee-tables';
import { REDEMPTION_STATUS_LABELS } from '@/modules/fund/lib/fund-payouts-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import {
	formatDateTime,
	formatNumber,
	formatSignedPercentValue,
	formatSignedPrice,
} from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';
import { cn } from '@/modules/ui/lib/utils';

type Agents = Record<string, FundAgentInfo | null>;

function agentName(agents: Agents | undefined, poolId: number) {
	return agents?.[String(poolId)]?.name ?? `Agente del fondo #${poolId}`;
}

// ======================================================================
// Pedidas (en cola o resueltas)
// ======================================================================

type RedemptionRequestsTableProps = {
	rows: RedemptionRequest[] | undefined;
	isLoading: boolean;
	error?: unknown;
	empty: string;
	/** Sin agentes no se muestra la columna Agente (vista de un solo agente). */
	agents?: Agents;
	/** Con usuarios se muestra la columna Persona (vista de staff). */
	users?: Map<number, UserSummary>;
	onCancel?: (request: RedemptionRequest) => void;
	isCanceling?: boolean;
};

export function RedemptionRequestsTable({
	rows,
	isLoading,
	error,
	empty,
	agents,
	users,
	onCancel,
	isCanceling,
}: RedemptionRequestsTableProps) {
	const columns: DataTableColumn<RedemptionRequest>[] = [
		{
			id: 'created',
			header: 'Pedida',
			className: 'whitespace-nowrap',
			cell: (row) => formatDateTime(row.created_at),
		},
		...(agents
			? [
					{
						id: 'agent',
						header: 'Agente',
						cell: (row: RedemptionRequest) => agentName(agents, row.pool_id),
					},
				]
			: []),
		...(users
			? [
					{
						id: 'user',
						header: 'Persona',
						cell: (row: RedemptionRequest) => (
							<OwnerCell userId={row.user_id} users={users} />
						),
					},
				]
			: []),
		{
			id: 'amount',
			header: 'Monto',
			className: 'text-right tabular-nums font-medium',
			cell: (row) =>
				row.amount === null ? 'Todo' : `${formatNumber(row.amount, 2)} USDT`,
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => (
				<Badge variant={row.status === 'queued' ? 'secondary' : 'outline'}>
					{REDEMPTION_STATUS_LABELS[row.status]}
				</Badge>
			),
		},
		{
			id: 'note',
			header: 'Nota',
			className: 'max-w-72',
			cell: (row) => row.note ?? '—',
		},
	];
	if (onCancel) {
		columns.push({
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) =>
				row.status === 'queued' ? (
					<Button
						variant="ghost"
						size="sm"
						disabled={isCanceling}
						onClick={() => onCancel(row)}
					>
						<IconX />
						Anular
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
			error={error}
			errorTitle="No pudimos cargar las salidas"
			empty={empty}
		/>
	);
}

// ======================================================================
// Lo que salió en cada liquidación, con su comisión
// ======================================================================

type RedemptionLinesTableProps = {
	rows: SettlementRedemption[] | undefined;
	isLoading: boolean;
	error?: unknown;
	agents?: Agents;
};

export function RedemptionLinesTable({
	rows,
	isLoading,
	error,
	agents,
}: RedemptionLinesTableProps) {
	const columns: DataTableColumn<SettlementRedemption>[] = [
		{
			id: 'created',
			header: 'Liquidación',
			className: 'whitespace-nowrap',
			cell: (row) => formatDateTime(row.created_at),
		},
		{
			id: 'agent',
			header: 'Agente',
			cell: (row) => agentName(agents, row.pool_id),
		},
		{
			id: 'cost',
			header: 'Aportaste',
			className: 'text-right tabular-nums',
			cell: (row) => formatNumber(row.cost, 2),
		},
		{
			id: 'value',
			header: 'Valía',
			className: 'text-right tabular-nums',
			cell: (row) => formatNumber(row.value, 2),
		},
		{
			id: 'gain',
			header: 'Ganancia',
			className: 'text-right tabular-nums',
			cell: (row) => (
				<span
					className={cn(
						Number(row.gain) >= 0 ? 'text-chart-1' : 'text-destructive',
					)}
				>
					{formatSignedPrice(row.gain)} (
					{formatSignedPercentValue(row.return_pct)})
				</span>
			),
		},
		{
			id: 'fee',
			header: 'Comisión',
			className: 'min-w-56',
			cell: (row) => (
				<div className="flex flex-col gap-1">
					<span className="tabular-nums">{formatNumber(row.fee, 2)} USDT</span>
					<FeeBreakdown breakdown={row.breakdown} />
				</div>
			),
		},
		{
			id: 'net',
			header: 'Recibiste',
			className: 'text-right tabular-nums font-medium',
			cell: (row) => (
				<div className="flex flex-col items-end">
					<span>{formatNumber(row.net, 2)} USDT</span>
					{row.pending_amount && Number(row.pending_amount) > 0 && (
						<span className="text-xs font-normal text-muted-foreground">
							{formatNumber(row.pending_amount, 2)} USDT aún sin la permanencia
							mínima
						</span>
					)}
				</div>
			),
		},
	];

	return (
		<DataTable
			columns={columns}
			rows={rows}
			getRowId={(row) => row.id}
			isLoading={isLoading}
			error={error}
			errorTitle="No pudimos cargar lo que salió de tus agentes"
			empty="Aún no ha salido dinero de tus agentes."
		/>
	);
}
