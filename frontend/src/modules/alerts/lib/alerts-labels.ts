import type {
	AlertChannels,
	AlertDeliveryStatus,
	AlertRuleType,
	AlertSeverity,
	PnlPeriod,
	PriceOperator,
	SignalActionFilter,
} from '@/modules/alerts/api/alerts.api';
import type { Bot } from '@/modules/bots/api/bots.api';
import type { MarketSymbol } from '@/modules/market/api/market.api';
import type { SelectOption } from '@/modules/shared/components/option-select';

type BadgeVariant = 'default' | 'secondary' | 'outline' | 'destructive';

const RULE_TYPE_LABELS: Record<AlertRuleType, string> = {
	signal: 'Señal',
	price: 'Precio',
	pnl: 'PnL',
	drawdown: 'Drawdown',
	error: 'Error del bot',
};

const RULE_TYPE_VARIANTS: Record<AlertRuleType, BadgeVariant> = {
	signal: 'default',
	price: 'secondary',
	pnl: 'secondary',
	drawdown: 'outline',
	error: 'destructive',
};

const RULE_TYPE_DESCRIPTIONS: Record<AlertRuleType, string> = {
	signal: 'Avisa cuando un bot emite una señal aprobada.',
	price: 'Avisa cuando el precio de un símbolo cruza el umbral.',
	pnl: 'Avisa cuando el PnL llega al porcentaje indicado.',
	drawdown: 'Avisa cuando la caída desde el máximo supera el porcentaje indicado.',
	error: 'Avisa cuando un bot entra en error o se rechaza una de sus órdenes.',
};

const SIGNAL_ACTION_LABELS: Record<SignalActionFilter, string> = {
	any: 'Cualquier señal',
	buy: 'Solo compra',
	sell: 'Solo venta',
	hold: 'Solo mantener',
};

const PRICE_OPERATOR_LABELS: Record<PriceOperator, string> = {
	lt: 'Menor que (<)',
	lte: 'Menor o igual que (≤)',
	gt: 'Mayor que (>)',
	gte: 'Mayor o igual que (≥)',
};

const PNL_PERIOD_LABELS: Record<PnlPeriod, string> = {
	daily: 'Diario',
	total: 'Total acumulado',
};

const SEVERITY_LABELS: Record<AlertSeverity, string> = {
	info: 'Informativa',
	warning: 'Advertencia',
	critical: 'Crítica',
};

const SEVERITY_VARIANTS: Record<AlertSeverity, BadgeVariant> = {
	info: 'secondary',
	warning: 'outline',
	critical: 'destructive',
};

const DELIVERY_LABELS: Record<AlertDeliveryStatus, string> = {
	pending: 'Pendiente',
	sent: 'Enviada',
	failed: 'Fallida',
};

const DELIVERY_VARIANTS: Record<AlertDeliveryStatus, BadgeVariant> = {
	pending: 'outline',
	sent: 'secondary',
	failed: 'destructive',
};

function toOptions(labels: Record<string, string>): SelectOption[] {
	return Object.entries(labels).map(([value, label]) => ({ value, label }));
}

const RULE_TYPE_OPTIONS = toOptions(RULE_TYPE_LABELS);
const SIGNAL_ACTION_OPTIONS = toOptions(SIGNAL_ACTION_LABELS);
const PRICE_OPERATOR_OPTIONS = toOptions(PRICE_OPERATOR_LABELS);
const PNL_PERIOD_OPTIONS = toOptions(PNL_PERIOD_LABELS);

/** Nombres de los canales activos, en el orden en que se muestran. */
function describeChannels(channels: AlertChannels | null | undefined): string[] {
	if (!channels) return [];
	const names: string[] = [];
	if (channels.email) names.push('Correo');
	if (channels.telegram) names.push('Telegram');
	if (channels.desktop) names.push('Escritorio');
	if (channels.webhook) names.push('Webhook');
	return names;
}

/** `Bot #12 · BTC/USDT` (el bot no tiene nombre propio). */
function botLabel(
	botId: number,
	bots: Bot[] | undefined,
	symbols: MarketSymbol[] | undefined,
): string {
	const bot = bots?.find((item) => item.id === botId);
	const symbol = bot
		? symbols?.find((item) => item.id === bot.symbol_id)?.symbol
		: undefined;
	return symbol ? `Bot #${botId} · ${symbol}` : `Bot #${botId}`;
}

function botOptions(
	bots: Bot[] | undefined,
	symbols: MarketSymbol[] | undefined,
): SelectOption[] {
	return (bots ?? []).map((bot) => ({
		value: String(bot.id),
		label: botLabel(bot.id, bots, symbols),
	}));
}

export type { BadgeVariant };
export {
	botLabel,
	botOptions,
	DELIVERY_LABELS,
	DELIVERY_VARIANTS,
	describeChannels,
	PNL_PERIOD_LABELS,
	PNL_PERIOD_OPTIONS,
	PRICE_OPERATOR_LABELS,
	PRICE_OPERATOR_OPTIONS,
	RULE_TYPE_DESCRIPTIONS,
	RULE_TYPE_LABELS,
	RULE_TYPE_OPTIONS,
	RULE_TYPE_VARIANTS,
	SEVERITY_LABELS,
	SEVERITY_VARIANTS,
	SIGNAL_ACTION_LABELS,
	SIGNAL_ACTION_OPTIONS,
};
