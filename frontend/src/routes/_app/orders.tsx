import { createFileRoute, redirect } from '@tanstack/react-router';

// Las órdenes viven dentro de cada agente (pestañas Órdenes y Posiciones);
// los agentes se listan en el inicio.
export const Route = createFileRoute('/_app/orders')({
	beforeLoad: () => {
		throw redirect({ to: '/dashboard', replace: true });
	},
});
