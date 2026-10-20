import { createFileRoute, redirect } from '@tanstack/react-router';

// Las órdenes viven dentro de cada agente (pestañas Órdenes y Posiciones).
export const Route = createFileRoute('/_app/orders')({
	beforeLoad: () => {
		throw redirect({ to: '/agents', replace: true });
	},
});
