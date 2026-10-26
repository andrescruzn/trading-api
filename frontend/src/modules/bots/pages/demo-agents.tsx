import { IconFlask, IconPlus } from '@tabler/icons-react';
import { useNavigate } from '@tanstack/react-router';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import { AgentsBoard } from '@/modules/bots/components/agents-board';
import { AgentsEmptyState } from '@/modules/bots/components/agents-empty-state';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';

// Agentes con dinero simulado: conviven con los reales (Inicio) y sirven para
// probar estrategias sin tocar la billetera de Binance ni el fondo.
export function DemoAgentsPage() {
	usePageBreadcrumb([{ label: 'Agentes demo' }]);
	const canManage = useCanManage();
	const navigate = useNavigate();

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Agentes demo"
				description="Agentes que operan con dinero simulado: escribes cuánto invertir y ves cómo le va a la estrategia, a la par de los agentes reales."
				actions={[
					{
						label: 'Crear agente demo',
						icon: <IconPlus />,
						onClick: () =>
							navigate({ to: '/agents/new', search: { mode: 'paper' } }),
						hidden: !canManage,
					},
				]}
			/>

			<Alert>
				<IconFlask />
				<AlertTitle>Dinero simulado</AlertTitle>
				<AlertDescription>
					Las órdenes de estos agentes no llegan a Binance ni mueven dinero de
					la billetera o del fondo.
				</AlertDescription>
			</Alert>

			<AgentsBoard
				mode="paper"
				emptyState={<AgentsEmptyState mode="paper" />}
			/>
		</div>
	);
}
