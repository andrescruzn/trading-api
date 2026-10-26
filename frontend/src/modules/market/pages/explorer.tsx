import { IconInfoCircle, IconRefresh, IconRobot } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import type {
	AssetClass,
	TrendDirection,
	TrendExplorerRow,
} from '@/modules/market/api/market.api';
import { useRefreshExplorerMutation } from '@/modules/market/hooks/use-market-mutations';
import { useTrendExplorerQuery } from '@/modules/market/hooks/use-market-queries';
import {
	ASSET_CLASS_LABELS,
	ASSET_CLASS_OPTIONS,
	TREND_DIRECTION_LABELS,
} from '@/modules/market/lib/market-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import {
	formatNumber,
	formatPercent,
	formatPrice,
} from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';
import { toast } from '@/modules/ui/components/toast';
import { cn } from '@/modules/ui/lib/utils';

const ALL = 'all';

function DirectionBadge({ direction }: { direction: TrendDirection }) {
	const label = TREND_DIRECTION_LABELS[direction];
	if (direction === 'up') {
		return (
			<Badge variant="outline" className="border-chart-1/40 text-chart-1">
				{label}
			</Badge>
		);
	}
	return (
		<Badge variant={direction === 'down' ? 'destructive' : 'secondary'}>
			{label}
		</Badge>
	);
}

/** Barra 0–100 + número: se compara de un vistazo entre filas. */
function StrengthBar({ value }: { value: number }) {
	return (
		<div className="flex items-center gap-2">
			<div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
				<div
					className="h-full rounded-full bg-primary"
					style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
				/>
			</div>
			<span className="tabular-nums">{formatNumber(value, 0)}</span>
		</div>
	);
}

function SignedPercent({ value }: { value: number | null }) {
	if (value === null) return <span className="text-muted-foreground">—</span>;
	return (
		<span
			className={cn(
				'tabular-nums',
				value > 0 && 'text-chart-1',
				value < 0 && 'text-destructive',
			)}
		>
			{value > 0 ? '+' : ''}
			{formatPercent(value, 1)}
		</span>
	);
}

const columns: DataTableColumn<TrendExplorerRow>[] = [
	{
		id: 'symbol',
		header: 'Símbolo',
		cell: (row) => (
			<div className="flex flex-col gap-0.5">
				<span className="font-mono font-medium">{row.symbol}</span>
				<span className="text-xs text-muted-foreground">
					{row.is_perpetual ? 'Perpetuo' : 'Spot'}
				</span>
			</div>
		),
	},
	{
		id: 'class',
		header: 'Clase',
		cell: (row) => (
			<Badge variant="secondary">{ASSET_CLASS_LABELS[row.asset_class]}</Badge>
		),
	},
	{
		id: 'direction',
		header: 'Tendencia',
		cell: (row) =>
			row.direction ? (
				<DirectionBadge direction={row.direction} />
			) : (
				<span className="text-sm text-muted-foreground">Sin datos</span>
			),
	},
	{
		id: 'strength',
		header: 'Fuerza',
		cell: (row) =>
			row.strength === null ? '—' : <StrengthBar value={row.strength} />,
	},
	{
		id: 'adx',
		header: 'ADX',
		className: 'text-right tabular-nums',
		cell: (row) => formatNumber(row.adx_14, 1),
	},
	{
		id: 'efficiency',
		header: 'Eficiencia',
		className: 'text-right tabular-nums',
		cell: (row) => formatPercent(row.efficiency_30, 0),
	},
	{
		id: 'ret30',
		header: '30 días',
		className: 'text-right',
		cell: (row) => <SignedPercent value={row.ret_30d} />,
	},
	{
		id: 'ret90',
		header: '90 días',
		className: 'text-right',
		cell: (row) => <SignedPercent value={row.ret_90d} />,
	},
	{
		id: 'atr',
		header: 'Volatilidad',
		className: 'text-right tabular-nums',
		cell: (row) => formatPercent(row.atr_pct_14, 1),
	},
	{
		id: 'close',
		header: 'Último cierre',
		className: 'text-right tabular-nums',
		cell: (row) => formatPrice(row.last_close),
	},
	{
		id: 'actions',
		header: <span className="sr-only">Acciones</span>,
		className: 'text-right',
		cell: (row) =>
			// La app no abre cortos: un mercado bajista solo se observa.
			row.direction === 'down' ? (
				<span className="text-xs text-muted-foreground">Solo observación</span>
			) : (
				<Button
					variant="ghost"
					size="sm"
					render={
						<Link to="/agents/new" search={{ symbol_id: row.symbol_id }} />
					}
				>
					<IconRobot />
					Crear agente
				</Button>
			),
	},
];

export function ExplorerPage() {
	usePageBreadcrumb([{ label: 'Explorar' }, { label: 'Explorar mercados' }]);
	// Descargar velas y crear agentes son acciones del super admin.
	const isAdmin = useCanManage();
	const [assetClass, setAssetClass] = useState<string>(ALL);

	const explorerQuery = useTrendExplorerQuery({
		asset_class: assetClass === ALL ? undefined : (assetClass as AssetClass),
	});
	const refreshMutation = useRefreshExplorerMutation();

	const rows = explorerQuery.data;
	const withoutData = rows?.filter((row) => !row.has_data).length ?? 0;
	const classOptions = [
		{ value: ALL, label: 'Todas las clases' },
		...ASSET_CLASS_OPTIONS,
	];

	function handleRefresh() {
		refreshMutation.mutate(undefined, {
			onSuccess: (result) =>
				toast.add({
					title: 'Datos actualizados',
					description:
						result.failed.length > 0
							? `No se pudieron descargar: ${result.failed.map((item) => item.symbol).join(', ')}.`
							: undefined,
					type: result.failed.length > 0 ? 'warning' : 'success',
				}),
			onError: (error) =>
				toast.add({
					title: 'No pudimos actualizar los datos',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Explorar mercados"
				description="Mercados ordenados por la fuerza de su tendencia en velas diarias. Úsalo para decidir dónde crear un agente."
				actions={[
					{
						label: refreshMutation.isPending
							? 'Actualizando…'
							: 'Actualizar datos',
						icon: <IconRefresh />,
						variant: 'outline',
						onClick: handleRefresh,
						disabled: refreshMutation.isPending,
						hidden: !isAdmin,
					},
				]}
			/>

			<Alert>
				<IconInfoCircle />
				<AlertTitle>Cómo leer la tabla</AlertTitle>
				<AlertDescription>
					<p>
						<strong>Fuerza</strong> (0–100) combina el ADX, que mide qué tan
						fuerte es la tendencia, con la eficiencia, que mide qué tan limpio
						es el movimiento: 100 % sería una línea recta. Una tendencia sin
						fuerza (ADX menor que 20) cuenta como lateral. Los mercados bajistas
						quedan al final porque la app solo abre compras. Los perpetuos
						siguen el precio del oro, el petróleo o una acción, y por ahora solo
						se operan en modo paper.
					</p>
					<p>
						Una tendencia fuerte en el pasado no garantiza que continúe: el
						agente igual filtra cada operación con la regla del 1 % y el
						riesgo/beneficio mínimo de 2:1.
					</p>
				</AlertDescription>
			</Alert>

			<div className="grid gap-3 sm:grid-cols-2 lg:max-w-xl">
				<OptionSelect
					aria-label="Clase de activo"
					size="sm"
					value={assetClass}
					onChange={(value) => setAssetClass(value ?? ALL)}
					options={classOptions}
				/>
			</div>

			{withoutData > 0 && (
				<p className="text-sm text-muted-foreground">
					{withoutData === 1
						? '1 mercado aún no tiene velas diarias suficientes.'
						: `${withoutData} mercados aún no tienen velas diarias suficientes.`}{' '}
					{isAdmin
						? 'Pulsa «Actualizar datos» para descargarlas.'
						: 'Se descargan solas una vez al día.'}
				</p>
			)}

			<DataTable
				columns={
					isAdmin
						? columns
						: columns.filter((column) => column.id !== 'actions')
				}
				rows={rows}
				getRowId={(row) => row.symbol_id}
				isLoading={explorerQuery.isLoading}
				error={explorerQuery.error}
				errorTitle="No pudimos cargar el explorador"
				empty="No hay mercados activos con ese filtro."
			/>
		</div>
	);
}
