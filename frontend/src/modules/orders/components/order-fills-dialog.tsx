import type { Order } from '@/modules/orders/api/orders.api';
import { FillsTable } from '@/modules/orders/components/fills-table';
import { useOrderFillsQuery } from '@/modules/orders/hooks/use-orders-queries';
import {
	ORDER_SIDE_LABELS,
	ORDER_TYPE_LABELS,
} from '@/modules/orders/lib/orders-labels';
import {
	Dialog,
	DialogBody,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
} from '@/modules/ui/components/dialog';

type OrderFillsDialogProps = {
	/** `null` = cerrado. */
	order: Order | null;
	onOpenChange: (open: boolean) => void;
};

/** Ejecuciones (fills) de una orden. */
export function OrderFillsDialog({
	order,
	onOpenChange,
}: OrderFillsDialogProps) {
	const fillsQuery = useOrderFillsQuery(order?.id ?? null);

	return (
		<Dialog open={!!order} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-3xl">
				<DialogHeader>
					<DialogTitle>Ejecuciones de la orden #{order?.id}</DialogTitle>
					<DialogDescription>
						{order
							? `${ORDER_SIDE_LABELS[order.side]} · ${ORDER_TYPE_LABELS[order.type]}`
							: ''}
					</DialogDescription>
				</DialogHeader>
				<DialogBody>
					<FillsTable
						fills={fillsQuery.data}
						isLoading={fillsQuery.isLoading}
						error={fillsQuery.error}
						empty="Esta orden aún no tiene ejecuciones."
						hideOrder
					/>
				</DialogBody>
			</DialogContent>
		</Dialog>
	);
}
