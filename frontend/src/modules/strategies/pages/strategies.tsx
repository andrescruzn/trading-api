import { IconEye } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import type { Strategy } from '@/modules/strategies/api/strategies.api';
import { StrategiesTable } from '@/modules/strategies/components/strategies-table';
import { StrategyDetailSheet } from '@/modules/strategies/components/strategy-detail-sheet';
import { useStrategiesQuery } from '@/modules/strategies/hooks/use-strategies-queries';
import { Button } from '@/modules/ui/components/button';

export function StrategiesPage() {
	usePageBreadcrumb([{ label: 'Trading' }, { label: 'Estrategias' }]);
	const strategiesQuery = useStrategiesQuery();
	// La estrategia elegida se conserva al cerrar para no vaciar el panel
	// mientras corre la animación de salida.
	const [selected, setSelected] = useState<Strategy | null>(null);
	const [detailOpen, setDetailOpen] = useState(false);

	function openDetail(strategy: Strategy) {
		setSelected(strategy);
		setDetailOpen(true);
	}

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Estrategias"
				description="Reglas objetivas que definen cuándo entrar y salir de una operación."
			/>
			<StrategiesTable
				rows={strategiesQuery.data}
				isLoading={strategiesQuery.isLoading}
				error={strategiesQuery.error}
				empty="Aún no hay estrategias disponibles. Un administrador debe crearlas."
				onRowClick={openDetail}
				renderActions={(strategy) => (
					<Button
						variant="ghost"
						size="sm"
						onClick={(event) => {
							event.stopPropagation();
							openDetail(strategy);
						}}
					>
						<IconEye />
						Ver
					</Button>
				)}
			/>
			<StrategyDetailSheet
				open={detailOpen}
				onOpenChange={setDetailOpen}
				strategy={selected}
			/>
		</div>
	);
}
