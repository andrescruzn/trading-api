import { createFileRoute, redirect } from '@tanstack/react-router';

// Los bots ahora se llaman agentes: la URL vieja lleva a la nueva.
export const Route = createFileRoute('/_app/bots')({
	beforeLoad: () => {
		throw redirect({ to: '/dashboard', replace: true });
	},
});
