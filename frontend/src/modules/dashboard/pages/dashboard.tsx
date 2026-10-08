import { IconBook, IconWallet } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import type { ReactNode } from 'react';
import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useAuth } from '@/modules/auth/hooks/use-auth';
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
import { useStrategiesQuery } from '@/modules/strategies/hooks/use-strategies-queries';
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

// Símbolos de referencia del inicio (los mismos que mostraba el dashboard anterior).
const MAIN_SYMBOL = 'BTC/USDT';
const SECONDARY_SYMBOL = 'ETH/USDT';
const SNAPSHOT_TIMEFRAME = '1h';

function RegimeBadge({ regime }: { regime: Regime | null }) {
	if (!regime) return null;
	return <Badge variant={REGIME_BADGE_VARIANT[regime]}>{regimeLabel(regime)}</Badge>;
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
	const strategiesQuery = useStrategiesQuery();

	const findSymbolId = (name: string) =>
		symbolsQuery.data?.find((symbol) => symbol.symbol === name)?.id;
	const mainSymbolId = findSymbolId(MAIN_SYMBOL);
	const secondarySymbolId = findSymbolId(SECONDARY_SYMBOL);
	const timeframeId = timeframesQuery.data?.find(
		(timeframe) => timeframe.code === SNAPSHOT_TIMEFRAME,
	)?.id;

	const mainSnapshot = useSymbolSnapshot(mainSymbolId, timeframeId);

	const accounts = accountsQuery.data ?? [];
	const paperCount = accounts.filter((account) => account.mode === 'paper').length;
	const liveCount = accounts.length - paperCount;

	const strategies = strategiesQuery.data ?? [];
	const trendCount = strategies.filter(
		(strategy) => strategy.parameters.strategy_type === 'trend_following',
	).length;
	const meanReversionCount = strategies.filter(
		(strategy) => strategy.parameters.strategy_type === 'mean_reversion',
	).length;

	const displayName = user?.full_name?.trim() || user?.email.split('@')[0];

	return (
		<div className="flex flex-col gap-6">
			<div>
				<h1 className="text-xl font-semibold">Hola, {displayName}</h1>
				<p className="text-sm text-muted-foreground">
					{user?.last_login_at
						? `Último ingreso: ${formatDateTime(user.last_login_at)}`
						: 'Este es el resumen de tu operación.'}
				</p>
			</div>

			<div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
				<SymbolCard label={MAIN_SYMBOL} symbolId={mainSymbolId} timeframeId={timeframeId} />
				<SymbolCard
					label={SECONDARY_SYMBOL}
					symbolId={secondarySymbolId}
					timeframeId={timeframeId}
				/>
				<StatCard
					label="Mis cuentas"
					icon={<IconWallet className="size-4" />}
					value={accounts.length}
					hint={`${paperCount} paper · ${liveCount} live`}
					isLoading={accountsQuery.isLoading}
				/>
				<StatCard
					label="Estrategias"
					icon={<IconBook className="size-4" />}
					value={strategies.length}
					hint={`${trendCount} de tendencia · ${meanReversionCount} de reversión`}
					isLoading={strategiesQuery.isLoading}
				/>
			</div>

			<Card>
				<CardHeader>
					<CardTitle>
						{MAIN_SYMBOL} · {SNAPSHOT_TIMEFRAME}
					</CardTitle>
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
						<div className="flex h-56 flex-col items-center justify-center gap-3 rounded-lg border border-dashed text-center text-sm text-muted-foreground">
							<p>
								Aún no hay velas de {MAIN_SYMBOL} en {SNAPSHOT_TIMEFRAME}.
							</p>
							<Button variant="outline" size="sm" render={<Link to="/market/symbols" />}>
								Ver símbolos
							</Button>
						</div>
					)}
				</CardContent>
			</Card>
		</div>
	);
}
