import { IconPlus } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { BotStatus } from '@/modules/bots/api/bots.api';
import { AgentCard } from '@/modules/bots/components/agent-card';
import { AgentsEmptyState } from '@/modules/bots/components/agents-empty-state';
import { useBotCatalogs } from '@/modules/bots/hooks/use-bot-catalogs';
import { useMyBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { Skeleton } from '@/modules/ui/components/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/modules/ui/components/tabs';

type StatusFilter = 'all' | 'active' | 'stopped';

const ACTIVE_STATUSES: BotStatus[] = ['running', 'paused'];

export function AgentsPage() {
	usePageBreadcrumb([{ label: 'Mis agentes' }]);
	const botsQuery = useMyBotsQuery();
	const { catalogs } = useBotCatalogs();
	const [filter, setFilter] = useState<StatusFilter>('all');

	const bots = botsQuery.data ?? [];
	const activeCount = bots.filter((bot) =>
		ACTIVE_STATUSES.includes(bot.status),
	).length;
	const visible = bots.filter((bot) => {
		if (filter === 'active') return ACTIVE_STATUSES.includes(bot.status);
		if (filter === 'stopped') return !ACTIVE_STATUSES.includes(bot.status);
		return true;
	});

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Mis agentes"
				description="Cada agente vigila un símbolo con una estrategia y le pide a la IA que confirme cada operación."
				actions={[
					{
						label: 'Nuevo agente',
						icon: <IconPlus />,
						render: <Link to="/agents/new" />,
					},
				]}
			/>

			{botsQuery.error ? (
				<ErrorAlert
					title="No pudimos cargar tus agentes"
					error={botsQuery.error}
				/>
			) : botsQuery.isLoading ? (
				<div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
					<Skeleton className="h-56 rounded-xl" />
					<Skeleton className="h-56 rounded-xl" />
					<Skeleton className="h-56 rounded-xl" />
				</div>
			) : bots.length === 0 ? (
				<AgentsEmptyState />
			) : (
				<>
					<Tabs
						value={filter}
						onValueChange={(value) => setFilter(value as StatusFilter)}
					>
						<TabsList>
							<TabsTrigger value="all">Todos ({bots.length})</TabsTrigger>
							<TabsTrigger value="active">Activos ({activeCount})</TabsTrigger>
							<TabsTrigger value="stopped">
								Detenidos ({bots.length - activeCount})
							</TabsTrigger>
						</TabsList>
					</Tabs>
					{visible.length === 0 ? (
						<p className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
							No hay agentes con ese estado.
						</p>
					) : (
						<div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
							{visible.map((bot) => (
								<AgentCard key={bot.id} bot={bot} catalogs={catalogs} />
							))}
						</div>
					)}
				</>
			)}
		</div>
	);
}
