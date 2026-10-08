import type { Position } from '@/modules/orders/api/orders.api';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { StatCard } from '@/modules/shared/components/stat-card';
import {
	formatDateTime,
	formatNumber,
	formatPrice,
	toNumber,
} from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import { cn } from '@/modules/ui/lib/utils';

type PositionsGridProps = {
	positions: Position[] | undefined;
	isLoading: boolean;
	error: unknown;
	/** `id → símbolo` para mostrar el nombre en vez del ID. */
	symbolNames: Map<number, string>;
};

/** P&L con signo y color: verde si gana, rojo si pierde. */
function PnlValue({ value }: { value: number | null }) {
	const number = toNumber(value);
	if (number === null) return <span>—</span>;
	return (
		<span
			className={cn(
				'font-medium tabular-nums',
				number > 0 && 'text-chart-1',
				number < 0 && 'text-destructive',
			)}
		>
			{number > 0 ? '+' : ''}
			{formatPrice(number)}
		</span>
	);
}

/** Posiciones del bot como tarjetas: cantidad, precio promedio y P&L realizado. */
export function PositionsGrid({
	positions,
	isLoading,
	error,
	symbolNames,
}: PositionsGridProps) {
	if (error) {
		return (
			<ErrorAlert title="No pudimos cargar las posiciones" error={error} />
		);
	}

	if (isLoading) {
		return (
			<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{Array.from({ length: 3 }, (_, index) => (
					<StatCard key={index} label="Posición" value={null} isLoading />
				))}
			</div>
		);
	}

	if (!positions?.length) {
		return (
			<p className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
				Este bot no tiene posiciones.
			</p>
		);
	}

	return (
		<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{positions.map((position) => (
				<StatCard
					key={position.id}
					label={
						symbolNames.get(position.symbol_id) ??
						`Símbolo #${position.symbol_id}`
					}
					icon={
						position.is_flat ? (
							<Badge variant="outline">Sin exposición</Badge>
						) : undefined
					}
					value={
						<span className="font-mono">{formatNumber(position.qty)}</span>
					}
					hint={
						<div className="flex w-full flex-col gap-1">
							<span>
								Precio promedio:{' '}
								<span className="font-medium text-foreground tabular-nums">
									{formatPrice(position.avg_price)}
								</span>
							</span>
							<span>
								{'P&L realizado: '}
								<PnlValue value={position.realized_pnl} />
							</span>
							<span className="text-xs">
								Actualizada: {formatDateTime(position.updated_at)}
							</span>
						</div>
					}
				/>
			))}
		</div>
	);
}
