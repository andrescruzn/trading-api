import { createFileRoute, redirect } from '@tanstack/react-router';

// El análisis puntual ahora vive en cada agente ("Analizar ahora").
export const Route = createFileRoute('/_app/agent')({
	beforeLoad: () => {
		throw redirect({ to: '/agents', replace: true });
	},
});
