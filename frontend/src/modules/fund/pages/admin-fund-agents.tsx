import { IconPlus } from '@tabler/icons-react';
import { useNavigate } from '@tanstack/react-router';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import { BotStatusBadge } from '@/modules/bots/components/bot-badges';
import type { FundPool } from '@/modules/fund/api/fund.api';
import { OpenPoolDialog } from '@/modules/fund/components/open-pool-dialog';
import { usePoolsQuery } from '@/modules/fund/hooks/use-fund-pools-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDateTime, formatNumber } from '@/modules/shared/lib/format';

const COLUMNS: DataTableColumn<FundPool>[] = [
	{
		id: 'agent',
		header: 'Agente',
		cell: (row) => (
			<div className="flex flex-col">
				<span className="font-medium">
					{row.agent?.name ?? `#${row.bot_id}`}
				</span>
				<span className="font-mono text-xs text-muted-foreground">
					{row.agent?.symbol ?? '—'}
				</span>
			</div>
		),
	},
	{
		id: 'status',
		header: 'Estado',
		cell: (row) =>
			row.agent ? <BotStatusBadge status={row.agent.status} /> : '—',
	},
	{
		id: 'nav',
		header: 'Valor unidad',
		className: 'text-right tabular-nums',
		cell: (row) => formatNumber(row.nav, 6),
	},
	{
		id: 'equity',
		header: 'Saldo liquidado',
		className: 'text-right tabular-nums',
		cell: (row) => `${formatNumber(row.equity, 2)} ${row.asset}`,
	},
	{
		id: 'capital',
		header: 'Capital hoy',
		className: 'text-right tabular-nums font-medium',
		cell: (row) => `${formatNumber(row.estimated_capital, 2)} ${row.asset}`,
	},
	{
		id: 'participants',
		header: 'Participantes',
		className: 'text-right tabular-nums',
		cell: (row) => row.participants,
	},
	{
		id: 'queued',
		header: 'En cola',
		className: 'text-right tabular-nums',
		cell: (row) =>
			Number(row.queued_total) > 0 ? (
				`${formatNumber(row.queued_total, 2)} ${row.asset}`
			) : (
				<span className="text-muted-foreground">—</span>
			),
	},
	{
		id: 'settled',
		header: 'Última liquidación',
		className: 'whitespace-nowrap',
		cell: (row) =>
			row.last_settled_at ? (
				formatDateTime(row.last_settled_at)
			) : (
				<span className="text-muted-foreground">Nunca</span>
			),
	},
];

/** Agentes que operan con el dinero del fondo (staff). */
export function AdminFundAgentsPage() {
	usePageBreadcrumb([
		{ label: 'Administración' },
		{ label: 'Agentes del fondo' },
	]);
	const canManage = useCanManage();
	const navigate = useNavigate();
	const poolsQuery = usePoolsQuery();
	const [opening, setOpening] = useState(false);

	function openDetail(poolId: number) {
		navigate({
			to: '/admin/fund-agents/$poolId',
			params: { poolId: String(poolId) },
		});
	}

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Agentes del fondo"
				description="Los agentes que operan con el dinero de los participantes. El dinero entra y sale de cada uno al liquidarlo, con el agente pausado y sin posiciones."
				actions={[
					{
						label: 'Abrir agente al fondo',
						icon: <IconPlus />,
						onClick: () => setOpening(true),
						hidden: !canManage,
					},
				]}
			/>
			<DataTable
				columns={COLUMNS}
				rows={poolsQuery.data}
				getRowId={(row) => row.id}
				isLoading={poolsQuery.isLoading}
				error={poolsQuery.error}
				errorTitle="No pudimos cargar los agentes del fondo"
				empty="Aún no hay agentes abiertos al fondo."
				onRowClick={(row) => openDetail(row.id)}
			/>
			<OpenPoolDialog
				open={opening}
				onOpenChange={setOpening}
				onOpened={openDetail}
			/>
		</div>
	);
}
