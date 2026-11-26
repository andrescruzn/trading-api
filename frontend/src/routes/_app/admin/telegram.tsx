import { createFileRoute, redirect } from '@tanstack/react-router';

// Telegram pasó a Administración → Notificaciones (con el correo).
export const Route = createFileRoute('/_app/admin/telegram')({
	beforeLoad: () => {
		throw redirect({ to: '/admin/notifications', replace: true });
	},
});
