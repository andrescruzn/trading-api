import { IconLoader2 } from '@tabler/icons-react';
import type { Order } from '@/modules/orders/api/orders.api';
import { useCancelOrderMutation } from '@/modules/orders/hooks/use-orders-mutations';
import { ORDER_TYPE_LABELS } from '@/modules/orders/lib/orders-labels';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from '@/modules/ui/components/alert-dialog';
import { toast } from '@/modules/ui/components/toast';

type CancelOrderDialogProps = {
	/** `null` = cerrado. */
	order: Order | null;
	onOpenChange: (open: boolean) => void;
};

export function CancelOrderDialog({
	order,
	onOpenChange,
}: CancelOrderDialogProps) {
	const cancelMutation = useCancelOrderMutation();
	const isNativeStop = order?.meta?.reason === 'stop_loss_native';

	function confirm() {
		if (!order) return;
		cancelMutation.mutate(order.id, {
			onSuccess: (updated) => {
				toast.add({
					title:
						updated.status === 'canceled'
							? 'Orden cancelada'
							: updated.status === 'filled'
								? 'La orden ya se había ejecutado'
								: 'Cancelación pedida',
					type: 'success',
				});
				onOpenChange(false);
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos cancelar la orden',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<AlertDialog open={!!order} onOpenChange={onOpenChange}>
			<AlertDialogContent>
				<AlertDialogHeader>
					<AlertDialogTitle>
						¿Cancelar la orden #{order?.id}
						{order ? ` (${ORDER_TYPE_LABELS[order.type] ?? order.type})` : ''}?
					</AlertDialogTitle>
					<AlertDialogDescription>
						{isNativeStop
							? 'Es el stop loss de la posición en el exchange. Si lo cancelas, la app sigue vigilando ese nivel, pero solo mientras esté funcionando.'
							: 'Lo que ya se haya ejecutado se mantiene; se cancela solo lo que queda abierto en el exchange.'}
					</AlertDialogDescription>
				</AlertDialogHeader>
				<AlertDialogFooter>
					<AlertDialogCancel>Volver</AlertDialogCancel>
					<AlertDialogAction
						variant="destructive"
						disabled={cancelMutation.isPending}
						onClick={confirm}
					>
						{cancelMutation.isPending && (
							<IconLoader2 className="animate-spin" />
						)}
						Cancelar orden
					</AlertDialogAction>
				</AlertDialogFooter>
			</AlertDialogContent>
		</AlertDialog>
	);
}
