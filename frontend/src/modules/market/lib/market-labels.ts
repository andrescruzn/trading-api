import type {
	AssetClass,
	ExchangeType,
	MarketSymbol,
	Timeframe,
} from '@/modules/market/api/market.api';
import type { SelectOption } from '@/modules/shared/components/option-select';

const ASSET_CLASS_LABELS: Record<AssetClass, string> = {
	crypto: 'Cripto',
	metal: 'Metal',
	etf: 'ETF',
	stock: 'Acción',
	forex: 'Forex',
};

const EXCHANGE_TYPE_LABELS: Record<ExchangeType, string> = {
	crypto_exchange: 'Exchange cripto',
	broker: 'Bróker',
	data_vendor: 'Proveedor de datos',
};

const ASSET_CLASS_OPTIONS: SelectOption[] = Object.entries(
	ASSET_CLASS_LABELS,
).map(([value, label]) => ({ value, label }));

const EXCHANGE_TYPE_OPTIONS: SelectOption[] = Object.entries(
	EXCHANGE_TYPE_LABELS,
).map(([value, label]) => ({ value, label }));

const CANDLE_LIMIT_OPTIONS: SelectOption[] = [50, 100, 200, 500].map(
	(limit) => ({ value: String(limit), label: `${limit} velas` }),
);

function symbolOptions(symbols: MarketSymbol[] | undefined): SelectOption[] {
	return (symbols ?? []).map((symbol) => ({
		value: String(symbol.id),
		label: symbol.exchange_name
			? `${symbol.symbol} · ${symbol.exchange_name}`
			: symbol.symbol,
	}));
}

function timeframeOptions(timeframes: Timeframe[] | undefined): SelectOption[] {
	return (timeframes ?? []).map((timeframe) => ({
		value: String(timeframe.id),
		label: timeframe.code,
	}));
}

/** `3600` → `1 hora`, `300` → `5 minutos`. */
function describeSeconds(seconds: number): string {
	const units: [number, string, string][] = [
		[86400 * 7, 'semana', 'semanas'],
		[86400, 'día', 'días'],
		[3600, 'hora', 'horas'],
		[60, 'minuto', 'minutos'],
	];
	for (const [size, singular, plural] of units) {
		if (seconds >= size && seconds % size === 0) {
			const count = seconds / size;
			return `${count} ${count === 1 ? singular : plural}`;
		}
	}
	return `${seconds} segundos`;
}

export {
	ASSET_CLASS_LABELS,
	ASSET_CLASS_OPTIONS,
	CANDLE_LIMIT_OPTIONS,
	describeSeconds,
	EXCHANGE_TYPE_LABELS,
	EXCHANGE_TYPE_OPTIONS,
	symbolOptions,
	timeframeOptions,
};
