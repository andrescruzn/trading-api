import { createFileRoute, redirect } from '@tanstack/react-router';

// Los agentes se listan en el inicio (con su filtro por estado).
export const Route = createFileRoute('/_app/agents/')({
	beforeLoad: () => {
		throw redirect({ to: '/dashboard', replace: true });
	},
});
