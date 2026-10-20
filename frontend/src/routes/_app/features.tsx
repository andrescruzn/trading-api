import { createFileRoute, redirect } from '@tanstack/react-router';

// Los indicadores de cada agente viven en su pestaña Mercado.
export const Route = createFileRoute('/_app/features')({
	beforeLoad: () => {
		throw redirect({ to: '/dashboard', replace: true });
	},
});
