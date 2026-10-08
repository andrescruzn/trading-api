import type {
	Bot,
	BotMode,
	BotStatus,
	BotTransition,
	SignalAction,
	SignalRejectionReason,
} from '@/modules/bots/api/bots.api';
import type { SelectOption } from '@/modules/shared/components/option-select';
import { formatNumber, toNumber } from '@/modules/shared/lib/format';

type BadgeVariant = 'default' | 'secondary' | 'outline' | 'destructive';

const BOT_STATUS_LABELS: Record<BotStatus, string> = {
	running: 'Activo',
	paused: 'Pausado',
	stopped: 'Detenido',
	error: 'Error',
};

const BOT_STATUS_VARIANTS: Record<BotStatus, BadgeVariant> = {
	running: 'default',
	paused: 'secondary',
	stopped: 'outline',
	error: 'destructive',
};

const BOT_MODE_LABELS: Record<BotMode, string> = {
	paper: 'Paper',
	live: 'Live',
};

const BOT_STATUS_OPTIONS: SelectOption[] = Object.entries(BOT_STATUS_LABELS).map(
	([value, label]) => ({ value, label }),
);

const BOT_MODE_OPTIONS: SelectOption[] = Object.entries(BOT_MODE_LABELS).map(
	([value, label]) => ({ value, label }),
);

/** Opciones del formulario: aclaran qué implica cada modo. */
const BOT_MODE_FORM_OPTIONS: SelectOption[] = [
	{ value: 'paper', label: 'Paper (simulado, sin dinero real)' },
	{ value: 'live', label: 'Live (dinero real)' },
];

/** Transiciones que acepta el backend desde cada estado. */
const BOT_TRANSITIONS: Record<BotStatus, BotTransition[]> = {
	stopped: ['start'],
	running: ['pause', 'stop'],
	paused: ['start', 'stop'],
	error: ['stop'],
};

function canTransition(status: BotStatus, transition: BotTransition): boolean {
	return BOT_TRANSITIONS[status]?.includes(transition) ?? false;
}

const SIGNAL_ACTION_LABELS: Record<SignalAction, string> = {
	buy: 'Compra',
	sell: 'Venta',
	hold: 'Mantener',
};

const SIGNAL_REJECTION_LABELS: Record<SignalRejectionReason, string> = {
	REGIME_MISMATCH: 'El régimen del mercado no es el que pide la estrategia.',
	RULES_NOT_MET: 'No se cumplen todas las reglas de la estrategia.',
	LLM_REJECTED: 'El agente de IA descartó la operación.',
	RR_RATIO_TOO_LOW: 'La operación no cumple el riesgo/beneficio mínimo de 2:1.',
};

function rejectionLabel(reason: string | null | undefined): string | null {
	if (!reason) return null;
	return SIGNAL_REJECTION_LABELS[reason as SignalRejectionReason] ?? reason;
}

/** `risk_params.risk_pct` como fracción (0.01 = 1 %), o `null` si falta. */
function getRiskPct(bot: Bot): number | null {
	const value = bot.risk_params?.risk_pct;
	if (typeof value !== 'number' && typeof value !== 'string') return null;
	return toNumber(value);
}

/** `2.4` → `2,4:1`. */
function formatRiskReward(value: number | string | null | undefined): string {
	const number = toNumber(value);
	if (number === null) return '—';
	return `${formatNumber(number, 2)}:1`;
}

/** Nombres para mostrar en vez de IDs (ver `useBotCatalogs`). */
type BotCatalogs = {
	accounts: Map<number, string>;
	symbols: Map<number, string>;
	timeframes: Map<number, string>;
	strategies: Map<number, string>;
};

/** `#12 · BTC/USDT · 4h`. */
function describeBot(bot: Bot, catalogs: BotCatalogs): string {
	const symbol = catalogs.symbols.get(bot.symbol_id);
	const timeframe = catalogs.timeframes.get(bot.timeframe_id);
	return [`#${bot.id}`, symbol, timeframe].filter(Boolean).join(' · ');
}

export type { BadgeVariant, BotCatalogs };
export {
	BOT_MODE_FORM_OPTIONS,
	BOT_MODE_LABELS,
	BOT_MODE_OPTIONS,
	BOT_STATUS_LABELS,
	BOT_STATUS_OPTIONS,
	BOT_STATUS_VARIANTS,
	canTransition,
	describeBot,
	formatRiskReward,
	getRiskPct,
	rejectionLabel,
	SIGNAL_ACTION_LABELS,
	SIGNAL_REJECTION_LABELS,
};
