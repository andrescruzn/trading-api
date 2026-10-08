import { useId } from 'react';
import type { Candle } from '@/modules/market/api/market.api';
import { formatDateTime, formatNumber } from '@/modules/shared/lib/format';
import { cn } from '@/modules/ui/lib/utils';

type PriceChartProps = {
	/** Velas en orden cronológico (de la más antigua a la más reciente). */
	candles: Candle[];
	className?: string;
};

const WIDTH = 640;
const HEIGHT = 220;
const PAD = { top: 12, right: 64, bottom: 24, left: 8 };

/**
 * Línea de precios de cierre en SVG (sin librería de gráficos). Verde si el
 * último cierre está por encima del primero, rojo si está por debajo; usa
 * solo tokens del tema (`--chart-1`, `--destructive`).
 */
export function PriceChart({ candles, className }: PriceChartProps) {
	const gradientId = useId();

	if (candles.length < 2) return null;

	const closes = candles.map((candle) => Number(candle.close));
	const min = Math.min(...closes);
	const max = Math.max(...closes);
	const range = max - min || 1;
	const plotWidth = WIDTH - PAD.left - PAD.right;
	const plotHeight = HEIGHT - PAD.top - PAD.bottom;

	const x = (index: number) =>
		PAD.left + (index / (closes.length - 1)) * plotWidth;
	const y = (price: number) =>
		PAD.top + (1 - (price - min) / range) * plotHeight;

	const line = closes
		.map((price, index) => `${x(index)},${y(price)}`)
		.join(' ');
	const area = `${PAD.left},${HEIGHT - PAD.bottom} ${line} ${x(closes.length - 1)},${HEIGHT - PAD.bottom}`;

	const isUp = closes[closes.length - 1] >= closes[0];
	const color = isUp ? 'var(--chart-1)' : 'var(--destructive)';
	const gridPrices = [0, 1, 2, 3].map((step) => min + (range * step) / 3);
	const timeIndexes = [
		0,
		Math.floor((candles.length - 1) / 2),
		candles.length - 1,
	];
	const lastX = x(closes.length - 1);
	const lastY = y(closes[closes.length - 1]);

	return (
		<svg
			viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
			className={cn('h-56 w-full', className)}
			role="img"
			aria-label={`Precio de cierre: de ${formatNumber(closes[0])} a ${formatNumber(closes[closes.length - 1])}`}
			preserveAspectRatio="none"
		>
			<defs>
				<linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
					<stop offset="0%" stopColor={color} stopOpacity={0.25} />
					<stop offset="100%" stopColor={color} stopOpacity={0} />
				</linearGradient>
			</defs>
			{gridPrices.map((price) => (
				<g key={price}>
					<line
						x1={PAD.left}
						x2={WIDTH - PAD.right}
						y1={y(price)}
						y2={y(price)}
						stroke="var(--border)"
						strokeDasharray="3 4"
					/>
					<text
						x={WIDTH - PAD.right + 6}
						y={y(price) + 4}
						className="fill-muted-foreground font-mono text-[10px]"
					>
						{formatNumber(price, 2)}
					</text>
				</g>
			))}
			{timeIndexes.map((index, position) => (
				<text
					key={index}
					x={x(index)}
					y={HEIGHT - 6}
					textAnchor={
						position === 0 ? 'start' : position === 2 ? 'end' : 'middle'
					}
					className="fill-muted-foreground text-[10px]"
				>
					{formatDateTime(candles[index].ts)}
				</text>
			))}
			<polygon points={area} fill={`url(#${gradientId})`} />
			<polyline
				points={line}
				fill="none"
				stroke={color}
				strokeWidth={2}
				strokeLinejoin="round"
				vectorEffect="non-scaling-stroke"
			/>
			<circle cx={lastX} cy={lastY} r={3.5} fill={color} />
		</svg>
	);
}
