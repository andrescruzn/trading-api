import { useEffect, useMemo, useRef, useState } from 'react';
import type { Candle } from '@/modules/market/api/market.api';
import type { PriceLevel } from '@/modules/market/lib/price-chart';
import {
	formatDate,
	formatDateTime,
	formatPrice,
	toNumber,
} from '@/modules/shared/lib/format';
import { cn } from '@/modules/ui/lib/utils';

// Una sola serie (cierres): sin leyenda, el título de la sección la nombra.
// La tabla de velas debajo es la vista accesible con todos los valores.

type PriceLineChartProps = {
	/** En cualquier orden: se ordenan por fecha. */
	candles: Candle[];
	/** Líneas de referencia (p. ej. entrada, stop loss y take profit). */
	levels?: PriceLevel[];
	className?: string;
};

const HEIGHT = 240;
const PAD = { top: 12, right: 72, bottom: 24, left: 8 };

const LEVEL_STROKE: Record<PriceLevel['tone'], string> = {
	neutral: 'stroke-muted-foreground',
	good: 'stroke-chart-1',
	critical: 'stroke-destructive',
};

function useWidth() {
	const ref = useRef<HTMLDivElement>(null);
	const [width, setWidth] = useState(0);
	useEffect(() => {
		const node = ref.current;
		if (!node) return;
		const observer = new ResizeObserver(([entry]) =>
			setWidth(entry.contentRect.width),
		);
		observer.observe(node);
		return () => observer.disconnect();
	}, []);
	return { ref, width };
}

/** 4 marcas "redondas" entre min y max. */
function niceTicks(min: number, max: number): number[] {
	const span = max - min || Math.abs(max) || 1;
	const raw = span / 3;
	const magnitude = 10 ** Math.floor(Math.log10(raw));
	const step =
		[1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= raw) ?? raw;
	const start = Math.ceil(min / step) * step;
	const ticks: number[] = [];
	for (let value = start; value <= max + step * 1e-9; value += step)
		ticks.push(value);
	return ticks;
}

export function PriceLineChart({
	candles,
	levels = [],
	className,
}: PriceLineChartProps) {
	const { ref, width } = useWidth();
	const [hover, setHover] = useState<number | null>(null);

	const points = useMemo(
		() =>
			[...candles]
				.sort((a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime())
				.map((candle) => ({ candle, close: toNumber(candle.close) ?? 0 })),
		[candles],
	);

	if (points.length < 2) return null;

	// La escala incluye los niveles para que SL/TP no queden fuera de vista
	const values = [...points.map((p) => p.close), ...levels.map((l) => l.value)];
	const rawMin = Math.min(...values);
	const rawMax = Math.max(...values);
	const margin = (rawMax - rawMin) * 0.05 || rawMax * 0.01 || 1;
	const min = rawMin - margin;
	const max = rawMax + margin;

	const plotWidth = Math.max(width - PAD.left - PAD.right, 1);
	const plotHeight = HEIGHT - PAD.top - PAD.bottom;
	const x = (i: number) => PAD.left + (i / (points.length - 1)) * plotWidth;
	const y = (value: number) =>
		PAD.top + (1 - (value - min) / (max - min)) * plotHeight;

	const line = points
		.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i)},${y(p.close)}`)
		.join(' ');
	const area = `${line} L${x(points.length - 1)},${PAD.top + plotHeight} L${x(0)},${PAD.top + plotHeight} Z`;
	const ticks = niceTicks(min, max);
	const last = points[points.length - 1];
	const active = hover !== null ? points[hover] : null;

	function onPointerMove(event: React.PointerEvent<SVGSVGElement>) {
		const box = event.currentTarget.getBoundingClientRect();
		const ratio = (event.clientX - box.left - PAD.left) / plotWidth;
		setHover(
			Math.min(
				Math.max(Math.round(ratio * (points.length - 1)), 0),
				points.length - 1,
			),
		);
	}

	function onKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
		if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
		event.preventDefault();
		const delta = event.key === 'ArrowLeft' ? -1 : 1;
		setHover((current) =>
			Math.min(
				Math.max((current ?? points.length - 1) + delta, 0),
				points.length - 1,
			),
		);
	}

	return (
		<div
			ref={ref}
			role="slider"
			tabIndex={0}
			aria-label="Precio de cierre por vela (usa las flechas para recorrerlas)"
			aria-valuemin={0}
			aria-valuemax={points.length - 1}
			aria-valuenow={hover ?? points.length - 1}
			aria-valuetext={`${formatDateTime((active ?? last).candle.ts)}: ${formatPrice((active ?? last).close)}`}
			onKeyDown={onKeyDown}
			onBlur={() => setHover(null)}
			className={cn(
				'relative w-full rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring',
				className,
			)}
		>
			{width > 0 && (
				<svg
					width={width}
					height={HEIGHT}
					aria-hidden
					className="touch-none"
					onPointerMove={onPointerMove}
					onPointerLeave={() => setHover(null)}
				>
					{/* Cuadrícula recesiva + marcas del eje (texto en token de texto) */}
					{ticks.map((tick) => (
						<g key={tick}>
							<line
								x1={PAD.left}
								x2={PAD.left + plotWidth}
								y1={y(tick)}
								y2={y(tick)}
								className="stroke-border"
								strokeWidth={1}
							/>
							<text
								x={PAD.left + plotWidth + 6}
								y={y(tick)}
								dy="0.32em"
								className="fill-muted-foreground text-[11px] tabular-nums"
							>
								{formatPrice(tick)}
							</text>
						</g>
					))}

					<path d={area} className="fill-primary/10" />
					<path
						d={line}
						fill="none"
						className="stroke-primary"
						strokeWidth={2}
						strokeLinejoin="round"
						strokeLinecap="round"
					/>

					{levels.map((level) => (
						<g key={level.label}>
							<line
								x1={PAD.left}
								x2={PAD.left + plotWidth}
								y1={y(level.value)}
								y2={y(level.value)}
								className={LEVEL_STROKE[level.tone]}
								strokeWidth={1.5}
							/>
							<text
								x={PAD.left + 4}
								y={y(level.value) - 4}
								className="fill-foreground text-[11px] font-medium"
							>
								{level.label} {formatPrice(level.value)}
							</text>
						</g>
					))}

					{/* Fechas: inicio y fin */}
					<text
						x={PAD.left}
						y={HEIGHT - 6}
						className="fill-muted-foreground text-[11px]"
					>
						{formatDate(points[0].candle.ts)}
					</text>
					<text
						x={PAD.left + plotWidth}
						y={HEIGHT - 6}
						textAnchor="end"
						className="fill-muted-foreground text-[11px]"
					>
						{formatDate(last.candle.ts)}
					</text>

					{/* Último cierre: punto final con anillo del color de la superficie */}
					{!active && (
						<circle
							cx={x(points.length - 1)}
							cy={y(last.close)}
							r={4}
							className="fill-primary stroke-card"
							strokeWidth={2}
						/>
					)}

					{active && hover !== null && (
						<g>
							<line
								x1={x(hover)}
								x2={x(hover)}
								y1={PAD.top}
								y2={PAD.top + plotHeight}
								className="stroke-muted-foreground"
								strokeWidth={1}
							/>
							<circle
								cx={x(hover)}
								cy={y(active.close)}
								r={4}
								className="fill-primary stroke-card"
								strokeWidth={2}
							/>
						</g>
					)}
				</svg>
			)}

			{active && hover !== null && (
				<div
					className="pointer-events-none absolute top-2 rounded-md border bg-popover px-2.5 py-1.5 text-xs text-popover-foreground shadow-sm"
					style={
						x(hover) > width / 2
							? { right: width - x(hover) + 12 }
							: { left: x(hover) + 12 }
					}
				>
					<p className="font-mono text-sm font-semibold tabular-nums">
						{formatPrice(active.close)}
					</p>
					<p className="text-muted-foreground">
						{formatDateTime(active.candle.ts)}
					</p>
					<p className="font-mono text-muted-foreground tabular-nums">
						A {formatPrice(active.candle.open)} · Máx{' '}
						{formatPrice(active.candle.high)} · Mín{' '}
						{formatPrice(active.candle.low)}
					</p>
				</div>
			)}
		</div>
	);
}
