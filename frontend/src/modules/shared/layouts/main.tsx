import { Outlet } from '@tanstack/react-router';
import { useEffect } from 'react';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import { PendingPage } from '@/modules/shared/components/pending-page';

export function MainLayout() {
	const { status, ensureLoaded } = useAuth();

	// Dispara la única petición a `/users/me` que necesita la app al arrancar.
	// `ensureLoaded` ya es idempotente (no reintenta si ya está resuelto o en
	// vuelo), así que no importa si este layout se remonta.
	useEffect(() => {
		ensureLoaded();
	}, [ensureLoaded]);

	if (status === 'idle' || status === 'loading') {
		return <PendingPage />;
	}

	return <Outlet />;
}
