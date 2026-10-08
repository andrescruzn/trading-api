import { IconDots, IconEye, IconPencil, IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import type { Strategy } from '@/modules/strategies/api/strategies.api';
import { StrategiesTable } from '@/modules/strategies/components/strategies-table';
import { StrategyDetailSheet } from '@/modules/strategies/components/strategy-detail-sheet';
import { StrategyFormDialog } from '@/modules/strategies/components/strategy-form-dialog';
import { useStrategiesQuery } from '@/modules/strategies/hooks/use-strategies-queries';
import { Button } from '@/modules/ui/components/button';
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
} from '@/modules/ui/components/dropdown-menu';

export function AdminStrategiesPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Estrategias' }]);
	const strategiesQuery = useStrategiesQuery();
	// `undefined` = diálogo cerrado; `null` = crear; una estrategia = editar.
	const [editing, setEditing] = useState<Strategy | null | undefined>(
		undefined,
	);
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
				description="Crea y edita las reglas con las que el sistema evalúa cada operación."
				actions={[
					{
						label: 'Nueva estrategia',
						icon: <IconPlus />,
						onClick: () => setEditing(null),
					},
				]}
			/>
			<StrategiesTable
				rows={strategiesQuery.data}
				isLoading={strategiesQuery.isLoading}
				error={strategiesQuery.error}
				empty="Aún no hay estrategias. Crea la primera para que los bots puedan operar con ella."
				onRowClick={openDetail}
				renderActions={(strategy) => (
					// Evita que abrir el menú dispare el clic de la fila (detalle).
					<div
						className="flex justify-end"
						onClick={(event) => event.stopPropagation()}
						onKeyDown={(event) => event.stopPropagation()}
					>
						<DropdownMenu>
							<DropdownMenuTrigger
								render={<Button variant="ghost" size="icon-sm" />}
							>
								<IconDots />
								<span className="sr-only">Acciones de {strategy.name}</span>
							</DropdownMenuTrigger>
							<DropdownMenuContent align="end" className="w-auto min-w-40">
								<DropdownMenuItem onClick={() => openDetail(strategy)}>
									<IconEye />
									Ver detalle
								</DropdownMenuItem>
								<DropdownMenuItem onClick={() => setEditing(strategy)}>
									<IconPencil />
									Editar
								</DropdownMenuItem>
							</DropdownMenuContent>
						</DropdownMenu>
					</div>
				)}
			/>
			<StrategyFormDialog
				open={editing !== undefined}
				onOpenChange={(open) => !open && setEditing(undefined)}
				strategy={editing ?? null}
			/>
			<StrategyDetailSheet
				open={detailOpen}
				onOpenChange={setDetailOpen}
				strategy={selected}
			/>
		</div>
	);
}
