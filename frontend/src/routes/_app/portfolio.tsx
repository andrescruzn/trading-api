import { createFileRoute, redirect } from '@tanstack/react-router';

// "Mis cuentas" ya no existe: la única billetera es la de Binance (se ve en
// Administración → Fondo → Billetera). La URL vieja lleva al inicio.
export const Route = createFileRoute('/_app/portfolio')({
	beforeLoad: () => {
		throw redirect({ to: '/dashboard', replace: true });
	},
});
