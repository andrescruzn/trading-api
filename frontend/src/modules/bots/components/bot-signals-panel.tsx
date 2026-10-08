import { IconBolt, IconLoader2, IconX } from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';
import type { Bot, Signal } from '@/modules/bots/api/bots.api';
import { SignalActionBadge } from '@/modules/bots/components/bot-badges';
import { SignalDetailSheet } from '@/modules/bots/components/signal-detail-sheet';
import { useGenerateSignalMutation } from '@/modules/bots/hooks/use-bots-mutations';
import { useSignalsQuery } from '@/modules/bots/hooks/use-bots-queries';
import {
	formatRiskReward,
	rejectionLabel,
	SIGNAL_ACTION_LABELS,
} from '@/modules/bots/lib/bots-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import {
	formatDateTime,
	formatPercent,
	formatPrice,
} from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardAction,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { toast } from '@/modules/ui/components/toast';

const columns: DataTableColumn<Signal>[] = [
	{
		id: 'ts',
		header: 'Fecha',
		cell: (row) => formatDateTime(row.ts),
		skeletonClassName: 'w-32',
	},
	{ id: 'action', header: 'Acción', cell: (row) => <SignalActionBadge action={row.action} /> },
	{
		id: 'approved',
		header: 'Estado',
		cell: (row) => (
			<Badge variant={row.approved ? 'secondary' : 'destructive'}>
				{row.approved ? 'Aprobada' : 'Rechazada'}
			</Badge>
		),
	},
	{
		id: 'entry',
		header: 'Entrada',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatPrice(row.entry_price),
	},
	{
		id: 'sl',
		header: 'SL',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatPrice(row.stop_loss),
	},
	{
		id: 'tp',
		header: 'TP',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatPrice(row.take_profit),
	},
	{
		id: 'rr',
		header: 'R/R',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatRiskReward(row.rr_ratio),
	},
	{
		id: 'confidence',
		header: 'Confianza',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => formatPercent(row.confidence, 0),
	},
];

type BotSignalsPanelProps = {
	bot: Bot;
	/** Ej. `#12 · BTC/USDT · 4h`. */
	botLabel: string;
	onClose: () => void;
};

/** Señales de un bot: generar una nueva con el agente y ver el detalle de cada una. */
export function BotSignalsPanel({ bot, botLabel, onClose }: BotSignalsPanelProps) {
	const signalsQuery = useSignalsQuery(bot.id);
	const generateMutation = useGenerateSignalMutation();
	const [selected, setSelected] = useState<Signal | null>(null);
	const isRunning = bot.status === 'running';
	const panelRef = useRef<HTMLDivElement>(null);

	// El panel aparece debajo de la tabla: se lleva a la vista al elegir un bot.
	useEffect(() => {
		panelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
	}, []);

	function handleGenerate() {
		generateMutation.mutate(bot.id, {
			onSuccess: (signal) => {
				toast.add({
					title: 'Señal generada',
					description: signal.approved
						? `${SIGNAL_ACTION_LABELS[signal.action]}: pasó todos los filtros.`
						: (rejectionLabel(signal.reasons?.rejection_reason) ??
							'La operación no pasó los filtros.'),
					type: signal.approved ? 'success' : 'info',
				});
				setSelected(signal);
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos generar la señal',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Card ref={panelRef}>
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<IconBolt className="size-4 text-muted-foreground" />
					Señales del bot {botLabel}
				</CardTitle>
				<CardDescription>
					{generateMutation.isPending
						? 'Analizando… El agente de IA puede tardar hasta un minuto.'
						: isRunning
							? 'Genera una señal para que el agente de IA evalúe el mercado con la estrategia del bot.'
							: 'Inicia el bot para generar señales.'}
				</CardDescription>
				<CardAction className="flex items-center gap-2">
					<Button
						size="sm"
						onClick={handleGenerate}
						disabled={!isRunning || generateMutation.isPending}
					>
						{generateMutation.isPending ? (
							<IconLoader2 className="animate-spin" />
						) : (
							<IconBolt />
						)}
						Generar señal
					</Button>
					<Button variant="ghost" size="icon-sm" onClick={onClose}>
						<IconX />
						<span className="sr-only">Cerrar señales</span>
					</Button>
				</CardAction>
			</CardHeader>
			<CardContent>
				<DataTable
					columns={columns}
					rows={signalsQuery.data}
					getRowId={(row) => row.id}
					isLoading={signalsQuery.isLoading}
					error={signalsQuery.error}
					errorTitle="No pudimos cargar las señales"
					empty="Este bot aún no tiene señales."
					onRowClick={setSelected}
				/>
			</CardContent>
			<SignalDetailSheet
				signal={selected}
				onOpenChange={(open) => !open && setSelected(null)}
			/>
		</Card>
	);
}
