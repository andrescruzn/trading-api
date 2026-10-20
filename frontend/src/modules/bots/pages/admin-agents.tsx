import { useNavigate } from '@tanstack/react-router';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { Bot } from '@/modules/bots/api/bots.api';
import { BotActionsMenu } from '@/modules/bots/components/bot-actions-menu';
import {
	BotModeBadge,
	BotStatusBadge,
} from '@/modules/bots/components/bot-badges';
import { useBotCatalogs } from '@/modules/bots/hooks/use-bot-catalogs';
import { useBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import {
	BOT_MODE_OPTIONS,
	BOT_STATUS_OPTIONS,
	describeBot,
	getRiskPct,
} from '@/modules/bots/lib/bots-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import {
	formatDate,
	formatDateTime,
	formatPercent,
} from '@/modules/shared/lib/format';

const ALL = 'all';

export function AdminAgentsPage() {
	usePageBreadcrumb([
		{ label: 'Administración' },
		{ label: 'Todos los agentes' },
	]);
	const navigate = useNavigate();
	// Sin filtros el backend devuelve todos los agentes (solo admin).
	const botsQuery = useBotsQuery();
	const { catalogs } = useBotCatalogs();
	const [status, setStatus] = useState(ALL);
	const [mode, setMode] = useState(ALL);

	const allBots = botsQuery.data ?? [];
	const filteredBots = allBots.filter(
		(bot) =>
			(status === ALL || bot.status === status) &&
			(mode === ALL || bot.mode === mode),
	);

	function openAgent(bot: Bot) {
		navigate({ to: '/agents/$agentId', params: { agentId: String(bot.id) } });
	}

	const columns: DataTableColumn<Bot>[] = [
		{
			id: 'name',
			header: 'Agente',
			cell: (row) => <span className="font-medium">{describeBot(row)}</span>,
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => <BotStatusBadge status={row.status} />,
		},
		{
			id: 'mode',
			header: 'Modo',
			cell: (row) => <BotModeBadge mode={row.mode} />,
		},
		{
			id: 'account',
			header: 'Cuenta',
			cell: (row) =>
				catalogs.accounts.get(row.account_id) ?? `#${row.account_id}`,
		},
		{
			id: 'symbol',
			header: 'Símbolo',
			cell: (row) => (
				<span className="font-mono font-medium">
					{catalogs.symbols.get(row.symbol_id) ?? `#${row.symbol_id}`}
				</span>
			),
		},
		{
			id: 'timeframe',
			header: 'Timeframe',
			className: 'font-mono',
			cell: (row) =>
				catalogs.timeframes.get(row.timeframe_id) ?? `#${row.timeframe_id}`,
		},
		{
			id: 'strategy',
			header: 'Estrategia',
			cell: (row) =>
				catalogs.strategies.get(row.strategy_id) ?? `#${row.strategy_id}`,
		},
		{
			id: 'risk',
			header: 'Riesgo',
			className: 'text-right font-mono tabular-nums',
			cell: (row) => formatPercent(getRiskPct(row)),
		},
		{
			id: 'started',
			header: 'Iniciado',
			cell: (row) => formatDateTime(row.started_at),
			skeletonClassName: 'w-32',
		},
		{
			id: 'created',
			header: 'Creado',
			cell: (row) => formatDate(row.created_at),
		},
		{
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) => <BotActionsMenu bot={row} onView={() => openAgent(row)} />,
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Todos los agentes"
				description={
					botsQuery.data
						? `Todos los agentes del sistema. ${filteredBots.length} de ${allBots.length} agentes.`
						: 'Todos los agentes del sistema.'
				}
			/>
			<div className="grid gap-3 sm:grid-cols-2 lg:max-w-xl">
				<OptionSelect
					aria-label="Estado"
					size="sm"
					value={status}
					onChange={(value) => setStatus(value ?? ALL)}
					options={[
						{ value: ALL, label: 'Todos los estados' },
						...BOT_STATUS_OPTIONS,
					]}
				/>
				<OptionSelect
					aria-label="Modo"
					size="sm"
					value={mode}
					onChange={(value) => setMode(value ?? ALL)}
					options={[
						{ value: ALL, label: 'Todos los modos' },
						...BOT_MODE_OPTIONS,
					]}
				/>
			</div>
			<DataTable
				columns={columns}
				rows={botsQuery.data ? filteredBots : undefined}
				getRowId={(row) => row.id}
				isLoading={botsQuery.isLoading}
				error={botsQuery.error}
				errorTitle="No pudimos cargar los agentes"
				empty={
					allBots.length > 0
						? 'No hay agentes con esos filtros.'
						: 'Aún no hay agentes en el sistema.'
				}
				onRowClick={openAgent}
			/>
		</div>
	);
}
