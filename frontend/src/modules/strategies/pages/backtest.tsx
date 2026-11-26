import { IconFlask, IconLoader2 } from '@tabler/icons-react';
import { getRouteApi } from '@tanstack/react-router';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import {
	useSymbolsQuery,
	useTimeframesQuery,
} from '@/modules/market/hooks/use-market-queries';
import {
	symbolOptions,
	timeframeOptions,
} from '@/modules/market/lib/market-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { StatCard } from '@/modules/shared/components/stat-card';
import {
	formatDate,
	formatDateTime,
	formatNumber,
	formatPercent,
	formatPrice,
	formatSignedPrice,
} from '@/modules/shared/lib/format';
import type {
	BacktestReport,
	BacktestTrade,
} from '@/modules/strategies/api/strategies.api';
import { useRunBacktestMutation } from '@/modules/strategies/hooks/use-strategies-mutations';
import { useStrategiesQuery } from '@/modules/strategies/hooks/use-strategies-queries';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';
import {
	Field,
	FieldDescription,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { cn } from '@/modules/ui/lib/utils';

const routeApi = getRouteApi('/_app/backtest');

const BAR_OPTIONS = [500, 1000, 2000, 3000].map((value) => ({
	value: String(value),
	label: `${value.toLocaleString('es-CO')} velas`,
}));

const EXIT_LABELS: Record<string, string> = {
	stop_loss: 'Stop loss',
	take_profit: 'Take profit',
	end: 'Fin del período',
};

function Signed({
	value,
	children,
}: {
	value: number | null;
	children: string;
}) {
	return (
		<span
			className={cn(
				'tabular-nums',
				value !== null && value > 0 && 'text-chart-1',
				value !== null && value < 0 && 'text-destructive',
			)}
		>
			{children}
		</span>
	);
}

const columns: DataTableColumn<BacktestTrade>[] = [
	{
		id: 'entry',
		header: 'Entrada',
		className: 'whitespace-nowrap',
		cell: (row) => formatDateTime(row.entry_ts),
		skeletonClassName: 'w-32',
	},
	{
		id: 'exit',
		header: 'Salida',
		className: 'whitespace-nowrap',
		cell: (row) => formatDateTime(row.exit_ts),
	},
	{
		id: 'prices',
		header: 'Precio entrada → salida',
		className: 'text-right font-mono tabular-nums',
		cell: (row) =>
			`${formatPrice(row.entry_price)} → ${formatPrice(row.exit_price)}`,
	},
	{
		id: 'reason',
		header: 'Cierre',
		cell: (row) => (
			<Badge
				variant={row.exit_reason === 'take_profit' ? 'secondary' : 'outline'}
			>
				{EXIT_LABELS[row.exit_reason ?? ''] ?? '—'}
			</Badge>
		),
	},
	{
		id: 'pnl',
		header: 'Resultado',
		className: 'text-right font-mono',
		cell: (row) => (
			<Signed value={row.pnl}>{formatSignedPrice(row.pnl)}</Signed>
		),
	},
	{
		id: 'return',
		header: 'Retorno',
		className: 'text-right font-mono',
		cell: (row) => (
			<Signed value={row.return_pct}>{formatPercent(row.return_pct)}</Signed>
		),
	},
];

function Results({ report }: { report: BacktestReport }) {
	const beatMarket =
		report.return_pct !== null &&
		report.buy_and_hold_pct !== null &&
		report.return_pct > report.buy_and_hold_pct;

	return (
		<div className="flex flex-col gap-6">
			<p className="text-sm text-muted-foreground">
				{report.strategy_name} · {report.bars.toLocaleString('es-CO')} velas del{' '}
				{formatDate(report.from_ts)} al {formatDate(report.to_ts)} ·{' '}
				{report.signals} velas cumplieron las reglas
				{report.skipped_in_position > 0
					? ` (${report.skipped_in_position} con una operación ya abierta)`
					: ''}
				.
			</p>
			<div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
				<StatCard
					label="Resultado"
					value={
						<Signed value={report.return_pct}>
							{formatPercent(report.return_pct)}
						</Signed>
					}
					hint={`${formatPrice(report.initial_capital)} → ${formatPrice(report.final_capital)} · comprar y mantener: ${formatPercent(report.buy_and_hold_pct)}`}
				/>
				<StatCard
					label="Operaciones ganadoras"
					value={formatPercent(report.win_rate, 0)}
					hint={`${report.wins} de ${report.trades} operaciones`}
				/>
				<StatCard
					label="R/R real"
					value={
						report.payoff_ratio !== null
							? `${formatNumber(report.payoff_ratio, 2)} : 1`
							: '—'
					}
					hint={`Profit factor ${report.profit_factor !== null ? formatNumber(report.profit_factor, 2) : '—'}`}
				/>
				<StatCard
					label="Caída máxima"
					value={formatPrice(report.max_drawdown)}
					hint={`Comisiones: ${formatPrice(report.total_fees)}`}
				/>
			</div>
			{report.trades > 0 && (
				<Alert>
					<IconFlask />
					<AlertTitle>
						{beatMarket
							? 'Le ganó a comprar y mantener en este período'
							: 'No le ganó a comprar y mantener en este período'}
					</AlertTitle>
					<AlertDescription>
						{report.trades < 30
							? 'Con menos de 30 operaciones el resultado puede ser suerte: prueba con más velas o un timeframe más corto.'
							: 'Un buen resultado en el pasado no garantiza el futuro. Antes de usar dinero real, compruébalo en paper.'}
					</AlertDescription>
				</Alert>
			)}
			<div className="flex flex-col gap-2">
				<h2 className="text-sm font-medium">Operaciones simuladas</h2>
				<DataTable
					columns={columns}
					rows={report.closed_trades}
					getRowId={(row) => `${row.entry_ts}-${row.exit_ts}`}
					isLoading={false}
					empty="La estrategia no encontró ninguna entrada en este período."
				/>
			</div>
		</div>
	);
}

export function BacktestPage() {
	usePageBreadcrumb([{ label: 'Explorar' }, { label: 'Backtesting' }]);
	const search = routeApi.useSearch();
	const strategiesQuery = useStrategiesQuery();
	const symbolsQuery = useSymbolsQuery({ is_active: true });
	const timeframesQuery = useTimeframesQuery();
	const runMutation = useRunBacktestMutation();

	const [strategyId, setStrategyId] = useState<string | null>(
		search.strategy_id ? String(search.strategy_id) : null,
	);
	const [symbolId, setSymbolId] = useState<string | null>(null);
	const [timeframeChoice, setTimeframeChoice] = useState<string | null>(null);
	const [bars, setBars] = useState('1000');
	const [capital, setCapital] = useState('10000');

	const strategy = strategiesQuery.data?.find(
		(item) => String(item.id) === strategyId,
	);
	// Por defecto, el timeframe que declara la estrategia
	const strategyTimeframeId = timeframesQuery.data?.find(
		(tf) => tf.code === strategy?.parameters.timeframe_code,
	)?.id;
	const timeframeId =
		timeframeChoice ??
		(strategyTimeframeId ? String(strategyTimeframeId) : null);

	// Solo símbolos de exchanges con descarga automática (la historia sale de allí)
	const symbols = (symbolsQuery.data ?? []).filter(
		(symbol) => symbol.supports_auto_fetch,
	);
	const strategyOptions = (strategiesQuery.data ?? []).map((item) => ({
		value: String(item.id),
		label: `${item.name} v${item.version}`,
	}));

	const capitalValue = Number(capital.replace(',', '.'));
	const canRun =
		!!strategyId &&
		!!symbolId &&
		!!timeframeId &&
		capitalValue > 0 &&
		!runMutation.isPending;

	function run() {
		if (!strategyId || !symbolId || !timeframeId) return;
		runMutation.mutate({
			strategy_id: Number(strategyId),
			symbol_id: Number(symbolId),
			timeframe_id: Number(timeframeId),
			bars: Number(bars),
			initial_capital: String(capitalValue),
		});
	}

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Backtesting"
				description="Prueba una estrategia en el pasado antes de usarla: aplica sus reglas vela a vela sobre la historia del exchange."
			/>
			<details className="rounded-xl border bg-card px-4 py-3 text-sm">
				<summary className="cursor-pointer font-medium marker:text-muted-foreground">
					¿Cómo se simula?
				</summary>
				<ul className="mt-3 flex list-disc flex-col gap-1.5 pl-5 text-muted-foreground">
					<li>
						Sin IA: mide si las reglas de la estrategia tienen ventaja, no las
						decisiones del agente.
					</li>
					<li>
						Cuando una vela cumple el régimen y todas las reglas, se compra al
						abrir la vela siguiente (nunca con información del futuro).
					</li>
					<li>
						Stop loss a 1,5 × ATR y take profit a 3 × ATR (2:1). Arriesga el 1 %
						del capital por operación y cobra 0,1 % de comisión por lado.
					</li>
					<li>
						Si una vela toca los dos niveles, cuenta el stop loss (el peor
						caso). Solo compras: en spot no hay ventas en corto.
					</li>
				</ul>
			</details>
			<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
				<Field className="lg:col-span-2">
					<FieldLabel htmlFor="backtest-strategy" required>
						Estrategia
					</FieldLabel>
					<OptionSelect
						id="backtest-strategy"
						value={strategyId}
						onChange={(value) => {
							setStrategyId(value);
							setTimeframeChoice(null);
						}}
						options={strategyOptions}
						placeholder="Elige una estrategia"
					/>
				</Field>
				<Field>
					<FieldLabel htmlFor="backtest-symbol" required>
						Símbolo
					</FieldLabel>
					<OptionSelect
						id="backtest-symbol"
						value={symbolId}
						onChange={setSymbolId}
						options={symbolOptions(symbols)}
						placeholder="Elige un símbolo"
					/>
				</Field>
				<Field>
					<FieldLabel htmlFor="backtest-timeframe" required>
						Timeframe
					</FieldLabel>
					<OptionSelect
						id="backtest-timeframe"
						value={timeframeId}
						onChange={setTimeframeChoice}
						options={timeframeOptions(timeframesQuery.data)}
						placeholder="Elige"
					/>
				</Field>
				<Field>
					<FieldLabel htmlFor="backtest-bars">Historia</FieldLabel>
					<OptionSelect
						id="backtest-bars"
						value={bars}
						onChange={(value) => setBars(value ?? '1000')}
						options={BAR_OPTIONS}
					/>
				</Field>
				<Field className="lg:col-span-2">
					<FieldLabel htmlFor="backtest-capital">Capital inicial</FieldLabel>
					<Input
						id="backtest-capital"
						inputMode="decimal"
						value={capital}
						onChange={(event) => setCapital(event.target.value)}
					/>
					<FieldDescription>
						En la moneda de cotización (USDT en BTC/USDT).
					</FieldDescription>
				</Field>
				<div className="flex items-end lg:col-span-3">
					<Button onClick={run} disabled={!canRun}>
						{runMutation.isPending ? (
							<IconLoader2 className="animate-spin" />
						) : (
							<IconFlask />
						)}
						{runMutation.isPending ? 'Simulando…' : 'Probar estrategia'}
					</Button>
				</div>
			</div>

			{runMutation.error ? (
				<ErrorAlert
					title="No pudimos hacer el backtest"
					error={runMutation.error}
				/>
			) : runMutation.data ? (
				<Results report={runMutation.data} />
			) : (
				<p className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
					Elige una estrategia, un símbolo y un timeframe para ver cómo le
					habría ido.
				</p>
			)}
		</div>
	);
}
