import type { ClosedTrade } from '@/modules/orders/api/orders.api';
import { useBotPerformanceQuery } from '@/modules/orders/hooks/use-orders-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { StatCard } from '@/modules/shared/components/stat-card';
import {
	formatDateTime,
	formatNumber,
	formatPercent,
	formatPrice,
	formatSignedPrice,
} from '@/modules/shared/lib/format';
import { cn } from '@/modules/ui/lib/utils';

// La regla del sistema: cada operación debe buscar al menos 2 de ganancia
// por cada 1 de riesgo. El R/R real se compara contra eso.
const TARGET_PAYOFF = 2;

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

const columns: DataTableColumn<ClosedTrade>[] = [
	{
		id: 'opened',
		header: 'Abierta',
		className: 'whitespace-nowrap',
		cell: (row) => formatDateTime(row.opened_at),
		skeletonClassName: 'w-32',
	},
	{
		id: 'closed',
		header: 'Cerrada',
		className: 'whitespace-nowrap',
		cell: (row) => formatDateTime(row.closed_at),
		skeletonClassName: 'w-32',
	},
	{
		id: 'qty',
		header: 'Cantidad',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatNumber(row.qty),
	},
	{
		id: 'cost',
		header: 'Invertido',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatPrice(row.cost),
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

/** Cómo le ha ido al agente: operaciones cerradas y sus métricas. */
export function AgentPerformanceTab({ botId }: { botId: number }) {
	const performanceQuery = useBotPerformanceQuery(botId);
	const data = performanceQuery.data;
	const isLoading = performanceQuery.isLoading;

	if (performanceQuery.error) {
		return (
			<ErrorAlert
				title="No pudimos calcular el rendimiento"
				error={performanceQuery.error}
			/>
		);
	}

	const hasOpen = !!data && data.open_qty > 0;

	return (
		<div className="flex flex-col gap-6">
			<div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
				<StatCard
					label="Resultado realizado"
					isLoading={isLoading}
					value={
						data ? (
							<Signed value={data.realized_pnl}>
								{formatSignedPrice(data.realized_pnl)}
							</Signed>
						) : (
							'—'
						)
					}
					hint={[
						hasOpen && data?.unrealized_pnl !== null
							? `Posición abierta: ${formatSignedPrice(data?.unrealized_pnl ?? null)} sin realizar`
							: 'De las operaciones cerradas',
						data?.funding_total
							? `Funding: ${formatSignedPrice(data.funding_total)}`
							: null,
					]
						.filter(Boolean)
						.join(' · ')}
				/>
				<StatCard
					label="Operaciones ganadoras"
					isLoading={isLoading}
					value={data ? formatPercent(data.win_rate, 0) : '—'}
					hint={
						data
							? `${data.wins} de ${data.trades} cerradas · ${data.losses} perdedoras`
							: undefined
					}
				/>
				<StatCard
					label="R/R real"
					isLoading={isLoading}
					value={
						data?.payoff_ratio != null
							? `${formatNumber(data.payoff_ratio, 2)} : 1`
							: '—'
					}
					hint={
						data?.payoff_ratio != null
							? data.payoff_ratio >= TARGET_PAYOFF
								? 'Cumple el objetivo de 2:1'
								: 'Por debajo del objetivo de 2:1'
							: 'Ganancia media / pérdida media (hace falta una de cada)'
					}
				/>
				<StatCard
					label="Profit factor"
					isLoading={isLoading}
					value={
						data?.profit_factor != null
							? formatNumber(data.profit_factor, 2)
							: '—'
					}
					hint={
						data
							? `Caída máxima: ${formatPrice(data.max_drawdown)} · retorno medio ${formatPercent(data.avg_return_pct)}`
							: undefined
					}
				/>
			</div>
			<div className="flex flex-col gap-2">
				<h3 className="text-sm font-medium">Operaciones cerradas</h3>
				<p className="text-sm text-muted-foreground">
					Una operación va desde que el agente compra hasta que vuelve a quedar
					sin posición. Las comisiones no se descuentan del resultado
					{data && data.total_fees > 0
						? ` (suman ${formatNumber(data.total_fees)} en el activo de cada comisión)`
						: ''}
					.
				</p>
				<DataTable
					columns={columns}
					rows={data?.closed_trades}
					getRowId={(row) => `${row.opened_at}-${row.closed_at}`}
					isLoading={isLoading}
					empty="Este agente aún no ha cerrado ninguna operación."
				/>
			</div>
		</div>
	);
}
