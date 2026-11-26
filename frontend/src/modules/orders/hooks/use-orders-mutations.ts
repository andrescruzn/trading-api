import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	cancelOrder,
	createOrder,
	type OrderInput,
} from '@/modules/orders/api/orders.api';
import {
	FILLS_QUERY_KEY,
	ORDERS_QUERY_KEY,
	POSITIONS_QUERY_KEY,
} from '@/modules/orders/hooks/use-orders-queries';

function useCreateOrderMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: OrderInput) => createOrder(input),
		// La orden se ejecuta al instante: también cambian ejecuciones y posiciones.
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ORDERS_QUERY_KEY });
			queryClient.invalidateQueries({ queryKey: FILLS_QUERY_KEY });
			queryClient.invalidateQueries({ queryKey: POSITIONS_QUERY_KEY });
		},
	});
}

/** Cancelar puede registrar ejecuciones de último momento: refresca todo. */
function useCancelOrderMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (id: number) => cancelOrder(id),
		onSettled: () => {
			queryClient.invalidateQueries({ queryKey: ORDERS_QUERY_KEY });
			queryClient.invalidateQueries({ queryKey: FILLS_QUERY_KEY });
			queryClient.invalidateQueries({ queryKey: POSITIONS_QUERY_KEY });
		},
	});
}

export { useCancelOrderMutation, useCreateOrderMutation };
