import { IconPlus, IconRobot, IconWallet } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import type { BotStatus } from '@/modules/bots/api/bots.api';
import { AgentCard } from '@/modules/bots/components/agent-card';
import { AgentsEmptyState } from '@/modules/bots/components/agents-empty-state';
import { PendingSignalsCard } from '@/modules/bots/components/pending-signals-card';
import { useBotCatalogs } from '@/modules/bots/hooks/use-bot-catalogs';
import { useMyBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { StatCard } from '@/modules/shared/components/stat-card';
import { formatDateTime } from '@/modules/shared/lib/format';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Button } from '@/modules/ui/components/button';
import { Skeleton } from '@/modules/ui/components/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/modules/ui/components/tabs';

type StatusFilter = 'all' | 'active' | 'stopped';

const ACTIVE_STATUSES: BotStatus[] = ['running', 'paused'];

// El inicio es la lista de agentes (antes también existía "Mis agentes"). El
// mercado de cada uno (precio, variación y régimen) va en su tarjeta; velas e
// indicadores, en la pestaña Mercado del agente.
export function DashboardPage() {
	const canManage = useCanManage();
	usePageBreadcrumb([]);
	const { user } = useAuth();
	const accountsQuery = useAccountsQuery();
	const botsQuery = useMyBotsQuery();
	const { catalogs } = useBotCatalogs();
	const [filter, setFilter] = useState<StatusFilter>('all');

	const bots = botsQuery.data ?? [];
	const activeBots = bots.filter((bot) => ACTIVE_STATUSES.includes(bot.status));
	const visibleBots = bots.filter((bot) => {
		if (filter === 'active') return ACTIVE_STATUSES.includes(bot.status);
		if (filter === 'stopped') return !ACTIVE_STATUSES.includes(bot.status);
		return true;
	});
	const runningCount = bots.filter((bot) => bot.status === 'running').length;
	const paperBots = bots.filter((bot) => bot.mode === 'paper').length;

	const ownAccounts = (accountsQuery.data ?? []).filter(
		(account) => account.user_id === user?.id,
	);
	const paperCount = ownAccounts.filter(
		(account) => account.mode === 'paper',
	).length;

	const displayName = user?.full_name?.trim() || user?.email.split('@')[0];
	const hasBots = bots.length > 0;

	let subtitle = 'Este es el resumen de tu operación.';
	if (hasBots) {
		subtitle =
			runningCount === 1
				? `1 de ${bots.length} agentes está analizando el mercado.`
				: `${runningCount} de ${bots.length} agentes están analizando el mercado.`;
	} else if (user?.last_login_at) {
		subtitle = `Último ingreso: ${formatDateTime(user.last_login_at)}`;
	}

	return (
		<div className="flex flex-col gap-8">
			<div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
				<div>
					<h1 className="text-2xl font-semibold tracking-tight">
						Hola, {displayName}
					</h1>
					<p className="text-sm text-muted-foreground">{subtitle}</p>
				</div>
				{hasBots && canManage && (
					<Button render={<Link to="/agents/new" />}>
						<IconPlus />
						Crear agente
					</Button>
				)}
			</div>

			{hasBots && <PendingSignalsCard />}

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
			) : !hasBots ? (
				<AgentsEmptyState />
			) : (
				<section className="flex flex-col gap-4">
					<div className="grid gap-4 sm:grid-cols-3">
						<StatCard
							label="Agentes activos"
							icon={<IconRobot className="size-4" />}
							value={`${activeBots.length} / ${bots.length}`}
							hint={`${runningCount} analizando · ${activeBots.length - runningCount} en pausa`}
						/>
						<StatCard
							label="Modo de operación"
							value={`${paperBots} en paper`}
							hint={`${bots.length - paperBots} en live (dinero real)`}
						/>
						<StatCard
							label="Mis cuentas"
							icon={<IconWallet className="size-4" />}
							value={ownAccounts.length}
							hint={`${paperCount} paper · ${ownAccounts.length - paperCount} live`}
							isLoading={accountsQuery.isLoading}
						/>
					</div>

					{activeBots.length === 0 && (
						<Alert>
							<IconRobot />
							<AlertTitle>Ningún agente está activo</AlertTitle>
							<AlertDescription>
								Inicia uno para que descargue velas y analice el mercado con su
								estrategia.
							</AlertDescription>
						</Alert>
					)}

					<div className="flex flex-wrap items-center justify-between gap-3">
						<h2 className="text-lg font-semibold">Tus agentes</h2>
						<Tabs
							value={filter}
							onValueChange={(value) => setFilter(value as StatusFilter)}
						>
							<TabsList>
								<TabsTrigger value="all">Todos ({bots.length})</TabsTrigger>
								<TabsTrigger value="active">
									Activos ({activeBots.length})
								</TabsTrigger>
								<TabsTrigger value="stopped">
									Detenidos ({bots.length - activeBots.length})
								</TabsTrigger>
							</TabsList>
						</Tabs>
					</div>
					{visibleBots.length === 0 ? (
						<p className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
							No hay agentes con ese estado.
						</p>
					) : (
						<div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
							{visibleBots.map((bot) => (
								<AgentCard key={bot.id} bot={bot} catalogs={catalogs} />
							))}
						</div>
					)}
				</section>
			)}
		</div>
	);
}
