import { createFileRoute, redirect } from '@tanstack/react-router';

// La plataforma opera solo con Binance: ya no hay catálogo de exchanges.
export const Route = createFileRoute('/_app/admin/exchanges')({
	beforeLoad: () => {
		throw redirect({ to: '/admin/symbols', replace: true });
	},
});
