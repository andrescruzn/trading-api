import { createFileRoute, redirect } from '@tanstack/react-router';

// Los bots ahora se llaman agentes: la URL vieja lleva a la nueva.
export const Route = createFileRoute('/_app/admin/bots')({
	beforeLoad: () => {
		throw redirect({ to: '/admin/agents', replace: true });
	},
});
