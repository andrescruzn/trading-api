import {
	IconArrowRight,
	IconPlus,
	IconRobot,
	IconWallet,
} from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import type { ReactNode } from 'react';
import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import { AgentCard } from '@/modules/bots/components/agent-card';
import { AgentsEmptyState } from '@/modules/bots/components/agents-empty-state';
import { useBotCatalogs } from '@/modules/bots/hooks/use-bot-catalogs';
import { useMyBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { PriceChart } from '@/modules/dashboard/components/price-chart';
import { useSymbolSnapshot } from '@/modules/dashboard/hooks/use-symbol-snapshot';
import {
	REGIME_BADGE_VARIANT,
	type Regime,
	regimeLabel,
} from '@/modules/features/lib/regime';
import {
	useSymbolsQuery,
	useTimeframesQuery,
} from '@/modules/market/hooks/use-market-queries';
import { StatCard } from '@/modules/shared/components/stat-card';
import {
	formatDateTime,
	formatPrice,
	formatSignedPercentValue,
} from '@/modules/shared/lib/format';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Badge } from '@/modules/ui/components/badge';
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
import { cn } from '@/modules/ui/lib/utils';

// Símbolos de referencia cuando la persona aún no tiene agentes.
const FALLBACK_SYMBOLS = ['BTC/USDT', 'ETH/USDT'];
const FALLBACK_TIMEFRAME = '1h';
// Agentes que se muestran en el inicio; el resto, en Mis agentes.
const DASHBOARD_AGENTS = 6;

type MarketPick = { symbolId?: number; timeframeId?: number; label: string };

function RegimeBadge({ regime }: { regime: Regime | null }) {
	if (!regime) return null;
	return (
		<Badge variant={REGIME_BADGE_VARIANT[regime]}>{regimeLabel(regime)}</Badge>
	);
}

function ChangeText({ value }: { value: number | null }) {
	if (value === null) return null;
	return (
		<span
			className={cn(
				'font-medium tabular-nums',
				value >= 0 ? 'text-chart-1' : 'text-destructive',
			)}
		>
			{formatSignedPercentValue(value)}
		</span>
	);
}

function SymbolCard({
	label,
	symbolId,
	timeframeId,
}: {
	label: string;
	symbolId?: number;
	timeframeId?: number;
}) {
	const snapshot = useSymbolSnapshot(symbolId, timeframeId);
	let hint: ReactNode = 'Sin velas guardadas';
	if (snapshot.hasData) {
		hint = (
			<>
				<ChangeText value={snapshot.changePct} />
				<RegimeBadge regime={snapshot.regime} />
			</>
		);
	}

	return (
		<StatCard
			label={label}
			value={snapshot.hasData ? formatPrice(snapshot.price) : '—'}
			hint={hint}
			isLoading={!!symbolId && snapshot.isLoading}
		/>
	);
}

export function DashboardPage() {
	usePageBreadcrumb([]);
	const { user } = useAuth();
	const symbolsQuery = useSymbolsQuery({ is_active: true });
	const timeframesQuery = useTimeframesQuery();
	const accountsQuery = useAccountsQuery();
	const botsQuery = useMyBotsQuery();
	const { catalogs } = useBotCatalogs();

	const bots = botsQuery.data ?? [];
	const activeBots = bots.filter(
		(bot) => bot.status === 'running' || bot.status === 'paused',
	);
	const runningCount = bots.filter((bot) => bot.status === 'running').length;
	const paperBots = bots.filter((bot) => bot.mode === 'paper').length;

	const ownAccounts = (accountsQuery.data ?? []).filter(
		(account) => account.user_id === user?.id,
	);
	const paperCount = ownAccounts.filter(
		(account) => account.mode === 'paper',
	).length;

	// Mercado: los pares que operan los agentes (sin repetir símbolo); si no
	// hay agentes, BTC y ETH en 1h como referencia.
	const marketPicks: MarketPick[] = [];
	for (const bot of bots) {
		if (marketPicks.length === 2) break;
		if (marketPicks.some((pick) => pick.symbolId === bot.symbol_id)) continue;
		marketPicks.push({
			symbolId: bot.symbol_id,
			timeframeId: bot.timeframe_id,
			label: [
				catalogs.symbols.get(bot.symbol_id),
				catalogs.timeframes.get(bot.timeframe_id),
			]
				.filter(Boolean)
				.join(' · '),
		});
	}
	if (marketPicks.length === 0) {
		const fallbackTimeframeId = timeframesQuery.data?.find(
			(timeframe) => timeframe.code === FALLBACK_TIMEFRAME,
		)?.id;
		for (const name of FALLBACK_SYMBOLS) {
			marketPicks.push({
				symbolId: symbolsQuery.data?.find((symbol) => symbol.symbol === name)
					?.id,
				timeframeId: fallbackTimeframeId,
				label: `${name} · ${FALLBACK_TIMEFRAME}`,
			});
		}
	}
	const mainPick = marketPicks[0];
	const mainSnapshot = useSymbolSnapshot(
		mainPick?.symbolId,
		mainPick?.timeframeId,
	);

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
				{hasBots && (
					<Button render={<Link to="/agents/new" />}>
						<IconPlus />
						Crear agente
					</Button>
				)}
			</div>

			{botsQuery.isLoading ? (
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

					<div className="flex items-center justify-between">
						<h2 className="text-lg font-semibold">Tus agentes</h2>
						{bots.length > DASHBOARD_AGENTS && (
							<Button variant="ghost" size="sm" render={<Link to="/agents" />}>
								Ver todos ({bots.length})
								<IconArrowRight />
							</Button>
						)}
					</div>
					<div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
						{bots.slice(0, DASHBOARD_AGENTS).map((bot) => (
							<AgentCard key={bot.id} bot={bot} catalogs={catalogs} />
						))}
					</div>
				</section>
			)}

			<section className="flex flex-col gap-4">
				<div>
					<h2 className="text-lg font-semibold">Mercado</h2>
					<p className="text-sm text-muted-foreground">
						{hasBots
							? 'Lo que están viendo tus agentes.'
							: 'Precios de referencia mientras creas tu primer agente.'}
					</p>
				</div>
				<div className="grid gap-4 sm:grid-cols-2">
					{marketPicks.map((pick) => (
						<SymbolCard
							key={pick.label}
							label={pick.label}
							symbolId={pick.symbolId}
							timeframeId={pick.timeframeId}
						/>
					))}
				</div>
				{mainPick && (
					<Card>
						<CardHeader>
							<CardTitle>{mainPick.label}</CardTitle>
							<CardDescription>Cierre de las últimas 48 velas.</CardDescription>
							<CardAction>
								<RegimeBadge regime={mainSnapshot.regime} />
							</CardAction>
						</CardHeader>
						<CardContent>
							{mainSnapshot.isLoading || symbolsQuery.isLoading ? (
								<Skeleton className="h-56 w-full" />
							) : mainSnapshot.candles.length >= 2 ? (
								<PriceChart candles={mainSnapshot.candles} />
							) : (
								<div className="flex h-56 flex-col items-center justify-center gap-3 rounded-lg border border-dashed p-4 text-center text-sm text-muted-foreground">
									<p>
										Aún no hay velas de {mainPick.label}. Se descargan solas
										mientras un agente que lo opera está activo.
									</p>
									<Button
										variant="outline"
										size="sm"
										render={<Link to={hasBots ? '/agents' : '/agents/new'} />}
									>
										{hasBots ? 'Ver mis agentes' : 'Crear agente'}
									</Button>
								</div>
							)}
						</CardContent>
					</Card>
				)}
			</section>
		</div>
	);
}
