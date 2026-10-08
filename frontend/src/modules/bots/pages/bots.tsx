import { IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { Bot } from '@/modules/bots/api/bots.api';
import { BotActionsMenu } from '@/modules/bots/components/bot-actions-menu';
import { BotModeBadge, BotStatusBadge } from '@/modules/bots/components/bot-badges';
import { BotFormDialog } from '@/modules/bots/components/bot-form-dialog';
import { BotSignalsPanel } from '@/modules/bots/components/bot-signals-panel';
import { useBotCatalogs } from '@/modules/bots/hooks/use-bot-catalogs';
import { useBotsByAccountsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { describeBot, getRiskPct } from '@/modules/bots/lib/bots-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDate, formatPercent } from '@/modules/shared/lib/format';

export function BotsPage() {
	usePageBreadcrumb([{ label: 'Trading' }, { label: 'Bots' }]);
	const { accountsQuery, catalogs } = useBotCatalogs();
	const accountIds = (accountsQuery.data ?? []).map((account) => account.id);
	const botsQuery = useBotsByAccountsQuery(accountIds);
	const [creating, setCreating] = useState(false);
	const [selectedBotId, setSelectedBotId] = useState<number | null>(null);

	// Se busca en la lista para que el panel refleje el estado más reciente
	// tras iniciar, pausar o detener el bot.
	const selectedBot = botsQuery.data?.find((bot) => bot.id === selectedBotId) ?? null;
	const hasAccounts = (accountsQuery.data?.length ?? 0) > 0;

	const columns: DataTableColumn<Bot>[] = [
		{ id: 'id', header: 'ID', className: 'w-16 font-mono', cell: (row) => `#${row.id}` },
		{ id: 'status', header: 'Estado', cell: (row) => <BotStatusBadge status={row.status} /> },
		{ id: 'mode', header: 'Modo', cell: (row) => <BotModeBadge mode={row.mode} /> },
		{
			id: 'account',
			header: 'Cuenta',
			cell: (row) => catalogs.accounts.get(row.account_id) ?? `#${row.account_id}`,
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
			cell: (row) => catalogs.timeframes.get(row.timeframe_id) ?? `#${row.timeframe_id}`,
		},
		{
			id: 'strategy',
			header: 'Estrategia',
			cell: (row) => catalogs.strategies.get(row.strategy_id) ?? `#${row.strategy_id}`,
		},
		{
			id: 'risk',
			header: 'Riesgo',
			className: 'text-right font-mono tabular-nums',
			cell: (row) => formatPercent(getRiskPct(row)),
		},
		{ id: 'created', header: 'Creado', cell: (row) => formatDate(row.created_at) },
		{
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) => (
				<BotActionsMenu bot={row} onViewSignals={() => setSelectedBotId(row.id)} />
			),
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Bots"
				description="Cada bot aplica una estrategia sobre un símbolo y genera señales que pasan las reglas de riesgo."
				actions={[
					{
						label: 'Nuevo bot',
						icon: <IconPlus />,
						onClick: () => setCreating(true),
						disabled: !hasAccounts,
					},
				]}
			/>
			<DataTable
				columns={columns}
				rows={botsQuery.data}
				getRowId={(row) => row.id}
				isLoading={accountsQuery.isLoading || botsQuery.isLoading}
				error={accountsQuery.error ?? botsQuery.error}
				errorTitle="No pudimos cargar los bots"
				empty={
					hasAccounts
						? 'Aún no tienes bots. Crea uno para que genere señales con tu estrategia.'
						: 'Aún no tienes cuentas. Crea una cuenta para poder crear bots.'
				}
				onRowClick={(row) => setSelectedBotId(row.id)}
			/>
			{selectedBot ? (
				<BotSignalsPanel
					key={selectedBot.id}
					bot={selectedBot}
					botLabel={describeBot(selectedBot, catalogs)}
					onClose={() => setSelectedBotId(null)}
				/>
			) : (
				(botsQuery.data?.length ?? 0) > 0 && (
					<p className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
						Elige un bot para ver sus señales.
					</p>
				)
			)}
			<BotFormDialog
				open={creating}
				onOpenChange={setCreating}
				onCreated={(bot) => setSelectedBotId(bot.id)}
			/>
		</div>
	);
}
