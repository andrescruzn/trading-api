import type { OrderSide, OrderStatus } from '@/modules/orders/api/orders.api';
import {
	ORDER_SIDE_LABELS,
	ORDER_STATUS_LABELS,
	ORDER_STATUS_VARIANTS,
} from '@/modules/orders/lib/orders-labels';
import { Badge } from '@/modules/ui/components/badge';

export function OrderSideBadge({ side }: { side: OrderSide }) {
	const label = ORDER_SIDE_LABELS[side] ?? side;
	if (side === 'buy') {
		return (
			<Badge variant="outline" className="border-chart-1/40 text-chart-1">
				{label}
			</Badge>
		);
	}
	return <Badge variant="destructive">{label}</Badge>;
}

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
	return (
		<Badge variant={ORDER_STATUS_VARIANTS[status] ?? 'outline'}>
			{ORDER_STATUS_LABELS[status] ?? status}
		</Badge>
	);
}
