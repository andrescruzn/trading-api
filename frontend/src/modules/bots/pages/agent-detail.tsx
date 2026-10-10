import {
	IconArrowLeft,
	IconCheck,
	IconClockHour4,
	IconLoader2,
	IconPencil,
	IconPlus,
	IconX,
} from '@tabler/icons-react';
import { getRouteApi, Link } from '@tanstack/react-router';
import { type ReactNode, useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { Bot, Signal } from '@/modules/bots/api/bots.api';
import { AgentControls } from '@/modules/bots/components/agent-controls';
import { AnalyzeNowButton } from '@/modules/bots/components/analyze-now-button';
import {
	AgentStatusDot,
	BotModeBadge,
	BotStatusBadge,
} from '@/modules/bots/components/bot-badges';
import { SignalDetailSheet } from '@/modules/bots/components/signal-detail-sheet';
import { SignalsTable } from '@/modules/bots/components/signals-table';
import { useBotCatalogs } from '@/modules/bots/hooks/use-bot-catalogs';
import { useUpdateBotMutation } from '@/modules/bots/hooks/use-bots-mutations';
import { useBotQuery } from '@/modules/bots/hooks/use-bots-queries';
import {
	describeBot,
	describeBotMarket,
	getRiskPct,
} from '@/modules/bots/lib/bots-labels';
import {
	useCandleFeaturesQuery,
	useFeatureSetsQuery,
} from '@/modules/features/hooks/use-features-queries';
import {
	INDICATOR_GROUP_HINTS,
	INDICATOR_GROUP_LABELS,
} from '@/modules/features/lib/features-labels';
import { regimeLabel } from '@/modules/features/lib/regime';
import type { Order } from '@/modules/orders/api/orders.api';
import { FillsTable } from '@/modules/orders/components/fills-table';
import { OrderFillsDialog } from '@/modules/orders/components/order-fills-dialog';
import { OrderFormDialog } from '@/modules/orders/components/order-form-dialog';
import { OrdersTable } from '@/modules/orders/components/orders-table';
import { PositionsGrid } from '@/modules/orders/components/positions-grid';
import {
	useBotFillsQuery,
	useBotOrdersQuery,
	useBotPositionsQuery,
} from '@/modules/orders/hooks/use-orders-queries';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { formatDateTime, formatPercent } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { useStrategiesQuery } from '@/modules/strategies/hooks/use-strategies-queries';
import {
	describeRule,
	strategyTypeLabel,
} from '@/modules/strategies/lib/strategies-labels';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { Input } from '@/modules/ui/components/input';
import { Skeleton } from '@/modules/ui/components/skeleton';
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from '@/modules/ui/components/tabs';
import { toast } from '@/modules/ui/components/toast';

const routeApi = getRouteApi('/_app/agents/$agentId');

// Mientras el agente espera sus primeros indicadores, se revisa cada 30 s.
const PREPARING_REFETCH_MS = 30_000;

// ======================================================================
// Cabecera: nombre editable
// ======================================================================

function AgentName({ bot }: { bot: Bot }) {
	const updateMutation = useUpdateBotMutation();
	const [editing, setEditing] = useState(false);
	const [draft, setDraft] = useState(bot.name);

	function save() {
		const name = draft.trim();
		if (!name || name === bot.name) {
			setEditing(false);
			return;
		}
		updateMutation.mutate(
			{ id: bot.id, input: { name } },
			{
				onSuccess: () => {
					toast.add({ title: 'Nombre actualizado', type: 'success' });
					setEditing(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos cambiar el nombre',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	if (editing) {
		return (
			<form
				className="flex items-center gap-2"
				onSubmit={(event) => {
					event.preventDefault();
					save();
				}}
			>
				<Input
					autoFocus
					value={draft}
					maxLength={80}
					onChange={(event) => setDraft(event.target.value)}
					aria-label="Nombre del agente"
					className="h-10 max-w-sm text-lg font-semibold"
				/>
				<Button
					type="submit"
					size="icon-sm"
					disabled={updateMutation.isPending}
				>
					{updateMutation.isPending ? (
						<IconLoader2 className="animate-spin" />
					) : (
						<IconCheck />
					)}
					<span className="sr-only">Guardar nombre</span>
				</Button>
				<Button
					variant="ghost"
					size="icon-sm"
					onClick={() => {
						setDraft(bot.name);
						setEditing(false);
					}}
				>
					<IconX />
					<span className="sr-only">Cancelar</span>
				</Button>
			</form>
		);
	}

	return (
		<div className="group flex min-w-0 items-center gap-2">
			<h1 className="truncate text-2xl font-semibold tracking-tight">
				{describeBot(bot)}
			</h1>
			<Button
				variant="ghost"
				size="icon-xs"
				className="opacity-60 group-hover:opacity-100"
				onClick={() => {
					setDraft(bot.name);
					setEditing(true);
				}}
			>
				<IconPencil />
				<span className="sr-only">Cambiar nombre</span>
			</Button>
		</div>
	);
}

// ======================================================================
// Aviso mientras llegan las primeras velas e indicadores
// ======================================================================

function PreparingNotice({ bot }: { bot: Bot }) {
	const isActive = bot.status === 'running' || bot.status === 'paused';
	const featuresQuery = useCandleFeaturesQuery(
		{
			symbol_id: bot.symbol_id,
			timeframe_id: bot.timeframe_id,
			feature_set_id: bot.feature_set_id ?? undefined,
			limit: 1,
		},
		{ refetchInterval: isActive ? PREPARING_REFETCH_MS : false },
	);
	const latest = featuresQuery.data?.[0];

	if (featuresQuery.isLoading) return null;

	if (!latest) {
		if (!isActive) {
			return (
				<Alert>
					<IconClockHour4 />
					<AlertTitle>El agente está detenido</AlertTitle>
					<AlertDescription>
						Inícialo para que descargue las velas de su símbolo y calcule los
						indicadores. Después podrás pedirle a la IA que analice el mercado.
					</AlertDescription>
				</Alert>
			);
		}
		return (
			<Alert>
				<IconLoader2 className="animate-spin" />
				<AlertTitle>Preparando datos</AlertTitle>
				<AlertDescription>
					El agente está descargando velas y calculando indicadores. Suele
					tardar uno o dos minutos; esta página se actualiza sola.
				</AlertDescription>
			</Alert>
		);
	}

	return (
		<p className="text-sm text-muted-foreground">
			Indicadores al día: última vela {formatDateTime(latest.ts)} · régimen{' '}
			<span className="font-medium text-foreground">
				{regimeLabel(latest.features.regime)}
			</span>
			.
		</p>
	);
}

// ======================================================================
// Pestañas
// ======================================================================

function OrdersTab({ bot, botLabel }: { bot: Bot; botLabel: string }) {
	const ordersQuery = useBotOrdersQuery(bot.id);
	const [fillsOrder, setFillsOrder] = useState<Order | null>(null);
	const [creating, setCreating] = useState(false);

	return (
		<div className="flex flex-col gap-3">
			<div className="flex justify-end">
				<Button size="sm" variant="outline" onClick={() => setCreating(true)}>
					<IconPlus />
					Nueva orden
				</Button>
			</div>
			<OrdersTable
				orders={ordersQuery.data}
				isLoading={ordersQuery.isLoading}
				error={ordersQuery.error}
				empty="Este agente aún no tiene órdenes."
				onViewFills={setFillsOrder}
			/>
			<OrderFillsDialog
				order={fillsOrder}
				onOpenChange={(open) => !open && setFillsOrder(null)}
			/>
			<OrderFormDialog
				open={creating}
				onOpenChange={setCreating}
				bot={bot}
				botLabel={botLabel}
			/>
		</div>
	);
}

function PositionsTab({
	botId,
	symbolNames,
}: {
	botId: number;
	symbolNames: Map<number, string>;
}) {
	const positionsQuery = useBotPositionsQuery(botId);
	const fillsQuery = useBotFillsQuery(botId);
	return (
		<div className="flex flex-col gap-6">
			<PositionsGrid
				positions={positionsQuery.data}
				isLoading={positionsQuery.isLoading}
				error={positionsQuery.error}
				symbolNames={symbolNames}
			/>
			<div className="flex flex-col gap-2">
				<h3 className="text-sm font-medium">Ejecuciones</h3>
				<FillsTable
					fills={fillsQuery.data}
					isLoading={fillsQuery.isLoading}
					error={fillsQuery.error}
					empty="Este agente aún no tiene ejecuciones."
				/>
			</div>
		</div>
	);
}

function ConfigItem({
	label,
	children,
}: {
	label: string;
	children: ReactNode;
}) {
	return (
		<div className="flex flex-col gap-1">
			<dt className="text-xs text-muted-foreground">{label}</dt>
			<dd className="text-sm font-medium">{children}</dd>
		</div>
	);
}

function ConfigTab({ bot, accountName }: { bot: Bot; accountName: string }) {
	const strategiesQuery = useStrategiesQuery();
	const featureSetsQuery = useFeatureSetsQuery();
	const strategy = strategiesQuery.data?.find(
		(item) => item.id === bot.strategy_id,
	);
	const featureSet = featureSetsQuery.data?.find(
		(item) => item.id === bot.feature_set_id,
	);
	const rules = strategy?.parameters.rules ?? [];

	return (
		<div className="grid gap-4 lg:grid-cols-2">
			<Card>
				<CardHeader>
					<CardTitle>Estrategia</CardTitle>
					<CardDescription>
						Las reglas que deben cumplirse antes de que la IA evalúe la
						operación.
					</CardDescription>
				</CardHeader>
				<CardContent className="flex flex-col gap-4">
					{strategiesQuery.isLoading ? (
						<Skeleton className="h-24 w-full" />
					) : strategy ? (
						<>
							<dl className="grid grid-cols-2 gap-4">
								<ConfigItem label="Nombre">
									{strategy.name} v{strategy.version}
								</ConfigItem>
								<ConfigItem label="Tipo">
									{strategyTypeLabel(strategy.parameters.strategy_type)}
								</ConfigItem>
								<ConfigItem label="Régimen requerido">
									{strategy.parameters.regime_required
										? regimeLabel(strategy.parameters.regime_required)
										: 'Cualquiera'}
								</ConfigItem>
								<ConfigItem label="Riesgo por operación">
									{formatPercent(getRiskPct(bot), 1)} del capital
								</ConfigItem>
								<ConfigItem label="Cuenta">
									<span className="inline-flex items-center gap-2">
										{accountName}
										<BotModeBadge mode={bot.mode} />
									</span>
								</ConfigItem>
								<ConfigItem label="Iniciado">
									{formatDateTime(bot.started_at)}
								</ConfigItem>
							</dl>
							{rules.length > 0 && (
								<div className="flex flex-col gap-2">
									<p className="text-xs text-muted-foreground">Reglas</p>
									<ul className="flex flex-wrap gap-1.5">
										{rules.map((rule) => (
											<li key={describeRule(rule)}>
												<Badge variant="outline" className="font-mono">
													{describeRule(rule)}
												</Badge>
											</li>
										))}
									</ul>
								</div>
							)}
						</>
					) : (
						<p className="text-sm text-muted-foreground">
							No encontramos la estrategia de este agente.
						</p>
					)}
				</CardContent>
			</Card>

			<Card>
				<CardHeader>
					<CardTitle>
						Indicadores{featureSet ? ` · ${featureSet.name}` : ''}
					</CardTitle>
					<CardDescription>
						Lo que la IA lee de cada vela para decidir.
					</CardDescription>
				</CardHeader>
				<CardContent>
					{featureSetsQuery.isLoading ? (
						<Skeleton className="h-24 w-full" />
					) : featureSet ? (
						<ul className="flex flex-col gap-3">
							{featureSet.indicators.map((group) => (
								<li key={group} className="flex flex-col gap-0.5">
									<span className="text-sm font-medium">
										{INDICATOR_GROUP_LABELS[group] ?? group}
									</span>
									<span className="text-sm text-muted-foreground">
										{INDICATOR_GROUP_HINTS[group]}
									</span>
								</li>
							))}
						</ul>
					) : (
						<p className="text-sm text-muted-foreground">
							Este agente no tiene un conjunto de indicadores.
						</p>
					)}
				</CardContent>
			</Card>
		</div>
	);
}

// ======================================================================
// Página
// ======================================================================

export function AgentDetailPage() {
	const { agentId } = routeApi.useParams();
	const id = Number(agentId);
	const botQuery = useBotQuery(Number.isInteger(id) && id > 0 ? id : null);
	const { catalogs } = useBotCatalogs();
	const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
	const bot = botQuery.data;

	usePageBreadcrumb([
		{ label: 'Mis agentes', href: '/agents' },
		{ label: bot ? describeBot(bot) : 'Agente' },
	]);

	if (botQuery.isLoading) {
		return (
			<div className="flex flex-col gap-6">
				<Skeleton className="h-10 w-72" />
				<Skeleton className="h-6 w-96" />
				<Skeleton className="h-64 w-full" />
			</div>
		);
	}

	if (!bot) {
		return (
			<div className="flex flex-col items-start gap-4">
				<ErrorAlert
					title="No pudimos abrir el agente"
					error={botQuery.error ?? new Error('No encontramos ese agente.')}
				/>
				<Button variant="outline" render={<Link to="/agents" />}>
					<IconArrowLeft />
					Volver a mis agentes
				</Button>
			</div>
		);
	}

	const accountName =
		catalogs.accounts.get(bot.account_id) ?? `Cuenta #${bot.account_id}`;
	const strategyName =
		catalogs.strategies.get(bot.strategy_id) ??
		`Estrategia #${bot.strategy_id}`;

	return (
		<div className="flex flex-col gap-6">
			<header className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
				<div className="flex min-w-0 flex-col gap-2">
					<div className="flex items-center gap-3">
						<AgentStatusDot status={bot.status} />
						<AgentName key={bot.name} bot={bot} />
					</div>
					<div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
						<BotStatusBadge status={bot.status} />
						<BotModeBadge mode={bot.mode} />
						<span className="font-mono font-medium text-foreground">
							{describeBotMarket(bot, catalogs)}
						</span>
						<span aria-hidden>·</span>
						<span>{strategyName}</span>
						<span aria-hidden>·</span>
						<span>{accountName}</span>
					</div>
				</div>
				<div className="flex flex-wrap items-center gap-2">
					<AnalyzeNowButton bot={bot} onResult={setSelectedSignal} />
					<AgentControls bot={bot} />
				</div>
			</header>

			<PreparingNotice bot={bot} />

			<Tabs defaultValue="signals">
				<TabsList>
					<TabsTrigger value="signals">Señales</TabsTrigger>
					<TabsTrigger value="orders">Órdenes</TabsTrigger>
					<TabsTrigger value="positions">Posiciones</TabsTrigger>
					<TabsTrigger value="config">Configuración</TabsTrigger>
				</TabsList>
				<TabsContent value="signals" className="pt-2">
					<SignalsTable botId={bot.id} onSelect={setSelectedSignal} />
				</TabsContent>
				<TabsContent value="orders" className="pt-2">
					<OrdersTab bot={bot} botLabel={describeBot(bot)} />
				</TabsContent>
				<TabsContent value="positions" className="pt-2">
					<PositionsTab botId={bot.id} symbolNames={catalogs.symbols} />
				</TabsContent>
				<TabsContent value="config" className="pt-2">
					<ConfigTab bot={bot} accountName={accountName} />
				</TabsContent>
			</Tabs>

			<SignalDetailSheet
				signal={selectedSignal}
				onOpenChange={(open) => !open && setSelectedSignal(null)}
			/>
		</div>
	);
}
