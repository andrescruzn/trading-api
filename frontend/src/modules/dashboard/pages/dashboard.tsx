import { IconPlus } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import { AgentsBoard } from '@/modules/bots/components/agents-board';
import { AgentsEmptyState } from '@/modules/bots/components/agents-empty-state';
import { PendingSignalsCard } from '@/modules/bots/components/pending-signals-card';
import { formatDateTime } from '@/modules/shared/lib/format';
import { Button } from '@/modules/ui/components/button';

// El inicio es la lista de agentes reales: los que operan la billetera de
// Binance del fondo. Los de dinero simulado viven en "Agentes demo". El
// mercado de cada uno (precio, variación y régimen) va en su tarjeta; velas e
// indicadores, en la pestaña Mercado del agente.
export function DashboardPage() {
	const canManage = useCanManage();
	usePageBreadcrumb([]);
	const { user } = useAuth();

	const displayName = user?.full_name?.trim() || user?.email.split('@')[0];
	const subtitle = user?.last_login_at
		? `Último ingreso: ${formatDateTime(user.last_login_at)}`
		: 'Estos son los agentes que operan con el dinero del fondo.';

	return (
		<div className="flex flex-col gap-8">
			<div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
				<div>
					<h1 className="text-2xl font-semibold tracking-tight">
						Hola, {displayName}
					</h1>
					<p className="text-sm text-muted-foreground">{subtitle}</p>
				</div>
				{canManage && (
					<Button render={<Link to="/agents/new" search={{ mode: 'live' }} />}>
						<IconPlus />
						Crear agente real
					</Button>
				)}
			</div>

			<PendingSignalsCard />

			<AgentsBoard mode="live" emptyState={<AgentsEmptyState mode="live" />} />
		</div>
	);
}
