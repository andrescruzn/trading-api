import { createFileRoute, redirect } from '@tanstack/react-router';

// Los símbolos se eligen al crear un agente; para comparar mercados está el
// explorador.
export const Route = createFileRoute('/_app/market/symbols')({
	beforeLoad: () => {
		throw redirect({ to: '/market/explorer', replace: true });
	},
});
