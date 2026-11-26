import { IconRobot } from '@tabler/icons-react';
import { type ReactNode, useState } from 'react';
import type { BotMode, BotStatus } from '@/modules/bots/api/bots.api';
import { AgentCard } from '@/modules/bots/components/agent-card';
import { useBotCatalogs } from '@/modules/bots/hooks/use-bot-catalogs';
import { useBotsByModeQuery } from '@/modules/bots/hooks/use-bots-queries';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { StatCard } from '@/modules/shared/components/stat-card';
import { formatPrice } from '@/modules/shared/lib/format';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Skeleton } from '@/modules/ui/components/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/modules/ui/components/tabs';

type StatusFilter = 'all' | 'active' | 'stopped';

const ACTIVE_STATUSES: BotStatus[] = ['running', 'paused'];

type AgentsBoardProps = {
	/** `live` = agentes reales (Inicio) · `paper` = agentes demo. */
	mode: BotMode;
	/** Lo que se ve cuando aún no hay agentes de este tipo. */
	emptyState: ReactNode;
};

/**
 * Lista de agentes de un tipo (reales o demo) con sus números y el filtro por
 * estado. Los dos tipos conviven: Inicio muestra los reales y "Agentes demo"
 * los de dinero simulado, cada uno con su propia lista.
 */
export function AgentsBoard({ mode, emptyState }: AgentsBoardProps) {
	const botsQuery = useBotsByModeQuery(mode);
	const { catalogs } = useBotCatalogs();
	const [filter, setFilter] = useState<StatusFilter>('all');

	if (botsQuery.error) {
		return (
			<ErrorAlert
				title="No pudimos cargar los agentes"
				error={botsQuery.error}
			/>
		);
	}

	if (botsQuery.isLoading) {
		return (
			<div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
				<Skeleton className="h-56 rounded-xl" />
				<Skeleton className="h-56 rounded-xl" />
				<Skeleton className="h-56 rounded-xl" />
			</div>
		);
	}

	const bots = botsQuery.data ?? [];
	if (bots.length === 0) return emptyState;

	const activeBots = bots.filter((bot) => ACTIVE_STATUSES.includes(bot.status));
	const runningCount = bots.filter((bot) => bot.status === 'running').length;
	const visibleBots = bots.filter((bot) => {
		if (filter === 'active') return ACTIVE_STATUSES.includes(bot.status);
		if (filter === 'stopped') return !ACTIVE_STATUSES.includes(bot.status);
		return true;
	});
	const simulatedTotal = bots.reduce(
		(sum, bot) => sum + Number(bot.demo_capital ?? 0),
		0,
	);

	return (
		<section className="flex flex-col gap-4">
			<div className="grid gap-4 sm:grid-cols-2">
				<StatCard
					label="Agentes activos"
					icon={<IconRobot className="size-4" />}
					value={`${activeBots.length} / ${bots.length}`}
					hint={`${runningCount} analizando · ${activeBots.length - runningCount} en pausa`}
				/>
				{mode === 'paper' ? (
					<StatCard
						label="Dinero simulado"
						value={formatPrice(simulatedTotal)}
						hint="Suma de lo que se puso en cada agente demo"
					/>
				) : (
					<StatCard
						label="Dinero"
						value="Billetera de Binance"
						hint="Cada agente opera con lo que se le asigna desde el fondo"
					/>
				)}
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
				<h2 className="text-lg font-semibold">
					{mode === 'paper' ? 'Agentes demo' : 'Agentes reales'}
				</h2>
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
	);
}
