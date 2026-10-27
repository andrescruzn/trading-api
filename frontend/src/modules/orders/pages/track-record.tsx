import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { SharedAgentsSection } from '@/modules/bots/components/shared-agents-section';
import type { StrategyTrackRecord } from '@/modules/orders/api/orders.api';
import { useStrategyTrackRecordQuery } from '@/modules/orders/hooks/use-orders-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatNumber, formatPercent } from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import { cn } from '@/modules/ui/lib/utils';

const ALL = 'all';

const MODE_OPTIONS = [
	{ value: ALL, label: 'Reales y demo' },
	{ value: 'live', label: 'Solo reales' },
	{ value: 'paper', label: 'Solo demo' },
];

function SignedPercent({ value }: { value: number | null }) {
	return (
		<span
			className={cn(
				'tabular-nums',
				value !== null && value > 0 && 'text-chart-1',
				value !== null && value < 0 && 'text-destructive',
			)}
		>
			{formatPercent(value)}
		</span>
	);
}

const NUMERIC = 'text-right font-mono';

const columns: DataTableColumn<StrategyTrackRecord>[] = [
	{
		id: 'strategy',
		header: 'Estrategia',
		cell: (row) => <span className="font-medium">{row.strategy_name}</span>,
		skeletonClassName: 'w-40',
	},
	{
		id: 'mode',
		header: 'Tipo',
		cell: (row) => (
			<Badge variant={row.mode === 'live' ? 'destructive' : 'secondary'}>
				{row.mode === 'live' ? 'Real' : 'Demo'}
			</Badge>
		),
	},
	{
		id: 'agents',
		header: 'Agentes',
		className: NUMERIC,
		cell: (row) => row.agents,
	},
	{
		id: 'trades',
		header: 'Operaciones',
		className: NUMERIC,
		cell: (row) => row.trades,
	},
	{
		id: 'win-rate',
		header: 'Ganadoras',
		className: NUMERIC,
		cell: (row) => formatPercent(row.win_rate, 0),
	},
	{
		id: 'avg-return',
		header: 'Retorno medio',
		className: NUMERIC,
		cell: (row) => <SignedPercent value={row.avg_return_pct} />,
	},
	{
		id: 'profit-factor',
		header: 'Profit factor',
		className: NUMERIC,
		cell: (row) =>
			row.profit_factor !== null ? formatNumber(row.profit_factor, 2) : '—',
	},
	{
		id: 'drawdown',
		header: 'Caída máxima',
		className: NUMERIC,
		cell: (row) => formatPercent(row.max_drawdown_pct),
	},
	{
		id: 'best-worst',
		header: 'Mejor / peor',
		className: NUMERIC,
		cell: (row) => (
			<span className="whitespace-nowrap">
				<SignedPercent value={row.best_trade_pct} /> /{' '}
				<SignedPercent value={row.worst_trade_pct} />
			</span>
		),
	},
];

export function TrackRecordPage() {
	usePageBreadcrumb([{ label: 'Explorar' }, { label: 'Track record' }]);
	const [mode, setMode] = useState(ALL);
	const trackRecordQuery = useStrategyTrackRecordQuery(
		mode === ALL ? undefined : (mode as 'paper' | 'live'),
	);

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Track record"
				description="Cómo le ha ido a cada estrategia sumando las operaciones cerradas de todos los agentes que la usan."
			/>
			<details className="rounded-xl border bg-card px-4 py-3 text-sm">
				<summary className="cursor-pointer font-medium marker:text-muted-foreground">
					¿Cómo leer esta tabla?
				</summary>
				<dl className="mt-3 grid gap-3 sm:grid-cols-2">
					<div className="flex flex-col gap-0.5">
						<dt className="font-medium">Retornos, no montos</dt>
						<dd className="text-muted-foreground">
							Cada operación cuenta por su retorno sobre lo invertido, así una
							cuenta grande no pesa más que una pequeña. No se muestra a quién
							pertenece cada agente.
						</dd>
					</div>
					<div className="flex flex-col gap-0.5">
						<dt className="font-medium">Profit factor</dt>
						<dd className="text-muted-foreground">
							Lo ganado dividido por lo perdido. Mayor que 1 significa que la
							estrategia gana más de lo que pierde.
						</dd>
					</div>
					<div className="flex flex-col gap-0.5">
						<dt className="font-medium">Caída máxima</dt>
						<dd className="text-muted-foreground">
							La peor racha: cuánto bajó la suma de retornos desde su punto más
							alto.
						</dd>
					</div>
					<div className="flex flex-col gap-0.5">
						<dt className="font-medium">¿Cuándo es confiable?</dt>
						<dd className="text-muted-foreground">
							Con pocas operaciones el resultado puede ser suerte. Lo
							recomendado es 100 o más operaciones en paper antes de pasar a
							live.
						</dd>
					</div>
				</dl>
			</details>
			<div className="grid gap-3 sm:max-w-xs">
				<OptionSelect
					aria-label="Modo"
					size="sm"
					value={mode}
					onChange={(value) => setMode(value ?? ALL)}
					options={MODE_OPTIONS}
				/>
			</div>
			<DataTable
				columns={columns}
				rows={trackRecordQuery.data}
				getRowId={(row) => `${row.strategy_id}-${row.mode}`}
				isLoading={trackRecordQuery.isLoading}
				error={trackRecordQuery.error}
				errorTitle="No pudimos cargar el track record"
				empty="Todavía ningún agente ha cerrado operaciones."
			/>
			<SharedAgentsSection />
		</div>
	);
}
