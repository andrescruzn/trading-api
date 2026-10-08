import type {
	OrderSide,
	OrderStatus,
	OrderType,
} from '@/modules/orders/api/orders.api';
import type { SelectOption } from '@/modules/shared/components/option-select';

type BadgeVariant = 'default' | 'secondary' | 'outline' | 'destructive';

const ORDER_SIDE_LABELS: Record<OrderSide, string> = {
	buy: 'Compra',
	sell: 'Venta',
};

const ORDER_TYPE_LABELS: Record<OrderType, string> = {
	market: 'Mercado',
	limit: 'Límite',
	stop: 'Stop',
	stop_limit: 'Stop límite',
};

const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
	new: 'Nueva',
	sent: 'Enviada',
	partially_filled: 'Ejecutada en parte',
	filled: 'Ejecutada',
	canceled: 'Cancelada',
	rejected: 'Rechazada',
};

const ORDER_STATUS_VARIANTS: Record<OrderStatus, BadgeVariant> = {
	new: 'outline',
	sent: 'outline',
	partially_filled: 'secondary',
	filled: 'default',
	canceled: 'outline',
	rejected: 'destructive',
};

function toOptions(labels: Record<string, string>): SelectOption[] {
	return Object.entries(labels).map(([value, label]) => ({ value, label }));
}

const ORDER_SIDE_OPTIONS = toOptions(ORDER_SIDE_LABELS);
const ORDER_TYPE_OPTIONS = toOptions(ORDER_TYPE_LABELS);
const ORDER_STATUS_OPTIONS = toOptions(ORDER_STATUS_LABELS);

/** `limit` y `stop_limit` llevan precio límite. */
function orderNeedsPrice(type: string | null | undefined): boolean {
	return type === 'limit' || type === 'stop_limit';
}

/** `stop` y `stop_limit` llevan precio de activación. */
function orderNeedsStopPrice(type: string | null | undefined): boolean {
	return type === 'stop' || type === 'stop_limit';
}

export {
	ORDER_SIDE_LABELS,
	ORDER_SIDE_OPTIONS,
	ORDER_STATUS_LABELS,
	ORDER_STATUS_OPTIONS,
	ORDER_STATUS_VARIANTS,
	ORDER_TYPE_LABELS,
	ORDER_TYPE_OPTIONS,
	orderNeedsPrice,
	orderNeedsStopPrice,
};
