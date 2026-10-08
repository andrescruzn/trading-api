/**
 * Formateo de números y fechas para la UI (locale `es-CO`).
 *
 * El backend serializa precios, cantidades y balances (`DECIMAL(30,12)`) como
 * string para no perder precisión: aquí se aceptan `string | number` y se
 * devuelve `'—'` para valores vacíos o no numéricos.
 */

const LOCALE = 'es-CO';
const EMPTY = '—';

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

function formatDateTime(iso: string | null | undefined): string {
	if (!iso) return EMPTY;
	const date = new Date(iso);
	if (Number.isNaN(date.getTime())) return EMPTY;
	return date.toLocaleString(LOCALE, {
		dateStyle: 'medium',
		timeStyle: 'short',
	});
}

function formatDate(iso: string | null | undefined): string {
	if (!iso) return EMPTY;
	const date = new Date(iso);
	if (Number.isNaN(date.getTime())) return EMPTY;
	return date.toLocaleDateString(LOCALE, { dateStyle: 'medium' });
}

export {
	EMPTY,
	formatDate,
	formatDateTime,
	formatNumber,
	formatPercent,
	formatPercentValue,
	formatPrice,
	formatSignedPercentValue,
	toNumber,
};
