import { createFileRoute, redirect } from '@tanstack/react-router';

// Las velas de cada agente viven en su pestaña Mercado.
export const Route = createFileRoute('/_app/market/candles')({
	beforeLoad: () => {
		throw redirect({ to: '/dashboard', replace: true });
	},
});
