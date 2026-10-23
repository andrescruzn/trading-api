/**
 * Formateo de números y fechas para la UI (locale `es-CO`).
 *
 * El backend serializa precios, cantidades y balances (`DECIMAL(30,12)`) como
 * string para no perder precisión: aquí se aceptan `string | number` y se
 * devuelve `'—'` para valores vacíos o no numéricos.
 *
 * Fechas: la BD guarda UTC y la API responde ISO 8601 con offset (`+00:00`).
 * Toda hora se pinta en hora de Colombia (`America/Bogota`, UTC-5), sin
 * importar la zona horaria del dispositivo.
 */

const LOCALE = 'es-CO';
const EMPTY = '—';
const APP_TIME_ZONE = 'America/Bogota';
/** Colombia no tiene horario de verano: el offset es fijo. */
const APP_UTC_OFFSET = '-05:00';
const OFFSET_SUFFIX = /(Z|[+-]\d{2}:?\d{2})$/i;

type Numeric = string | number | null | undefined;

function toNumber(value: Numeric): number | null {
	if (value === null || value === undefined || value === '') return null;
	const parsed = typeof value === 'number' ? value : Number(value);
	return Number.isFinite(parsed) ? parsed : null;
}

/**
 * Número con separadores de miles. Por defecto ajusta los decimales a la
 * magnitud: precios grandes con 2, precios de centavos con hasta 8.
 */
function formatNumber(value: Numeric, maximumFractionDigits?: number): string {
	const number = toNumber(value);
	if (number === null) return EMPTY;
	const digits =
		maximumFractionDigits ??
		(Math.abs(number) >= 1000 ? 2 : Math.abs(number) >= 1 ? 4 : 8);
	return number.toLocaleString(LOCALE, { maximumFractionDigits: digits });
}

/** Precio con símbolo `$` (cotizaciones en USD/USDT). */
function formatPrice(value: Numeric): string {
	const number = toNumber(value);
	if (number === null) return EMPTY;
	return `$${formatNumber(number, Math.abs(number) >= 1 ? 2 : 6)}`;
}

/** Monto con signo: `+$12,50` / `-$3,20` (P&L). */
function formatSignedPrice(value: Numeric): string {
	const number = toNumber(value);
	if (number === null) return EMPTY;
	const sign = number > 0 ? '+' : number < 0 ? '-' : '';
	return `${sign}${formatPrice(Math.abs(number))}`;
}

/** `0.0123` → `1,23 %`. Para valores que ya vienen en %, usa `formatPercentValue`. */
function formatPercent(ratio: Numeric, fractionDigits = 2): string {
	const number = toNumber(ratio);
	if (number === null) return EMPTY;
	return number.toLocaleString(LOCALE, {
		style: 'percent',
		maximumFractionDigits: fractionDigits,
	});
}

/** `1.5` → `1,5 %` (el valor ya está expresado en porcentaje). */
function formatPercentValue(value: Numeric, fractionDigits = 2): string {
	const number = toNumber(value);
	if (number === null) return EMPTY;
	return `${number.toLocaleString(LOCALE, { maximumFractionDigits: fractionDigits })} %`;
}

/** Variación con signo: `+2,35 %` / `-0,80 %`. */
function formatSignedPercentValue(value: Numeric, fractionDigits = 2): string {
	const number = toNumber(value);
	if (number === null) return EMPTY;
	const sign = number > 0 ? '+' : '';
	return `${sign}${number.toFixed(fractionDigits).replace('.', ',')} %`;
}

/**
 * Fecha de la API → `Date`. Si llega sin offset (`2026-10-23T15:00:00`) se
 * asume UTC: `new Date()` la tomaría como hora local del dispositivo.
 */
function parseApiDate(iso: string | null | undefined): Date | null {
	if (!iso) return null;
	const normalized =
		iso.includes('T') && !OFFSET_SUFFIX.test(iso) ? `${iso}Z` : iso;
	const date = new Date(normalized);
	return Number.isNaN(date.getTime()) ? null : date;
}

/** Milisegundos epoch de una fecha de la API (para ordenar o contar). */
function toTimestamp(iso: string | null | undefined): number | null {
	return parseApiDate(iso)?.getTime() ?? null;
}

function formatDateTime(iso: string | null | undefined): string {
	const date = parseApiDate(iso);
	if (!date) return EMPTY;
	return date.toLocaleString(LOCALE, {
		dateStyle: 'medium',
		timeStyle: 'short',
		timeZone: APP_TIME_ZONE,
	});
}

/** Como `formatDateTime` pero con segundos (auditoría, orden exacto). */
function formatDateTimeSeconds(iso: string | null | undefined): string {
	const date = parseApiDate(iso);
	if (!date) return EMPTY;
	return date.toLocaleString(LOCALE, {
		dateStyle: 'medium',
		timeStyle: 'medium',
		timeZone: APP_TIME_ZONE,
	});
}

function formatDate(iso: string | null | undefined): string {
	const date = parseApiDate(iso);
	if (!date) return EMPTY;
	return date.toLocaleDateString(LOCALE, {
		dateStyle: 'medium',
		timeZone: APP_TIME_ZONE,
	});
}

/** `2026-10-23 10:00:00` en hora de Colombia: para CSV y archivos. */
function formatTimestamp(iso: string | null | undefined): string {
	const date = parseApiDate(iso);
	if (!date) return '';
	// `sv-SE` da el orden ISO (`AAAA-MM-DD HH:mm:ss`) que entienden las hojas de cálculo.
	return date.toLocaleString('sv-SE', { timeZone: APP_TIME_ZONE });
}

/** Día de hoy en Colombia como `AAAA-MM-DD`. */
function todayInAppTimeZone(): string {
	return new Date().toLocaleDateString('sv-SE', { timeZone: APP_TIME_ZONE });
}

/** `AAAA-MM-DD` (p. ej. de un `<input type="date">`) → inicio de ese día en Colombia, en ISO UTC. */
function startOfAppDayIso(day: string): string {
	return new Date(`${day}T00:00:00${APP_UTC_OFFSET}`).toISOString();
}

/** Inicio del día siguiente en Colombia, en ISO UTC (fin exclusivo de un rango). */
function startOfNextAppDayIso(day: string): string {
	const date = new Date(`${day}T00:00:00${APP_UTC_OFFSET}`);
	date.setUTCDate(date.getUTCDate() + 1);
	return date.toISOString();
}

export {
	APP_TIME_ZONE,
	EMPTY,
	formatDate,
	formatDateTime,
	formatDateTimeSeconds,
	formatNumber,
	formatPercent,
	formatPercentValue,
	formatPrice,
	formatSignedPercentValue,
	formatSignedPrice,
	formatTimestamp,
	parseApiDate,
	startOfAppDayIso,
	startOfNextAppDayIso,
	todayInAppTimeZone,
	toNumber,
	toTimestamp,
};
