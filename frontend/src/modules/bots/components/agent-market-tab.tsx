import { IconLoader2, IconRefresh } from '@tabler/icons-react';
import { useState } from 'react';
import type { Bot } from '@/modules/bots/api/bots.api';
import { useSyncBotMarketMutation } from '@/modules/bots/hooks/use-bots-mutations';
import { CandleFeaturesTable } from '@/modules/features/components/candle-features-table';
import { IndicatorsGlossary } from '@/modules/features/components/indicators-glossary';
import { useCandleFeaturesQuery } from '@/modules/features/hooks/use-features-queries';
import { CandlesTable } from '@/modules/market/components/candles-table';
import { useCandlesQuery } from '@/modules/market/hooks/use-market-queries';
import { CANDLE_LIMIT_OPTIONS } from '@/modules/market/lib/market-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { formatNumber } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button } from '@/modules/ui/components/button';
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from '@/modules/ui/components/tabs';
import { toast } from '@/modules/ui/components/toast';

// Velas e indicadores solo existen para el símbolo y timeframe de un agente
// activo (el scheduler los descarga y calcula por él), así que se muestran
// aquí, sin selectores. "Actualizar datos" fuerza esa misma descarga y
// cálculo (sirve también con el agente detenido).

function emptyMessage(bot: Bot, what: 'velas' | 'indicadores') {
	const isActive = bot.status === 'running' || bot.status === 'paused';
	return isActive
		? `Preparando ${what}. Suele tardar uno o dos minutos.`
		: `Aún no hay ${what}. Pulsa Actualizar datos o inicia el agente.`;
}

function CandlesPanel({ bot, limit }: { bot: Bot; limit: number }) {
	const candlesQuery = useCandlesQuery({
		symbol_id: bot.symbol_id,
		timeframe_id: bot.timeframe_id,
		limit,
	});
	return (
		<CandlesTable
			rows={candlesQuery.data}
			isLoading={candlesQuery.isLoading}
			error={candlesQuery.error}
			empty={emptyMessage(bot, 'velas')}
		/>
	);
}

function IndicatorsPanel({ bot, limit }: { bot: Bot; limit: number }) {
	const featuresQuery = useCandleFeaturesQuery({
		symbol_id: bot.symbol_id,
		timeframe_id: bot.timeframe_id,
		feature_set_id: bot.feature_set_id ?? undefined,
		limit,
	});
	return (
		<div className="flex flex-col gap-3">
			<IndicatorsGlossary />
			<CandleFeaturesTable
				rows={featuresQuery.data}
				isLoading={featuresQuery.isLoading}
				error={featuresQuery.error}
				empty={emptyMessage(bot, 'indicadores')}
			/>
		</div>
	);
}

function SyncMarketButton({ bot }: { bot: Bot }) {
	const syncMutation = useSyncBotMarketMutation();

	function sync() {
		syncMutation.mutate(bot.id, {
			onSuccess: (result) =>
				toast.add({
					title: 'Datos actualizados',
					description:
						result.rows_calculated === null
							? `Se descargaron ${formatNumber(result.rows_fetched, 0)} velas.`
							: `Se descargaron ${formatNumber(result.rows_fetched, 0)} velas y se recalcularon los indicadores.`,
					type: 'success',
				}),
			onError: (error) =>
				toast.add({
					title: 'No pudimos actualizar los datos',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Button
			size="sm"
			variant="outline"
			onClick={sync}
			disabled={syncMutation.isPending}
		>
			{syncMutation.isPending ? (
				<IconLoader2 className="animate-spin" />
			) : (
				<IconRefresh />
			)}
			{syncMutation.isPending ? 'Actualizando…' : 'Actualizar datos'}
		</Button>
	);
}

export function AgentMarketTab({ bot }: { bot: Bot }) {
	const [limit, setLimit] = useState('100');

	return (
		<Tabs defaultValue="candles" className="gap-3">
			<div className="flex flex-wrap items-center justify-between gap-3">
				<TabsList variant="line">
					<TabsTrigger value="candles">Velas</TabsTrigger>
					<TabsTrigger value="indicators">Indicadores</TabsTrigger>
				</TabsList>
				<div className="flex items-center gap-2">
					<OptionSelect
						aria-label="Cantidad de velas"
						size="sm"
						value={limit}
						onChange={(value) => setLimit(value ?? '100')}
						options={CANDLE_LIMIT_OPTIONS}
						className="w-36"
					/>
					<SyncMarketButton bot={bot} />
				</div>
			</div>
			<TabsContent value="candles">
				<CandlesPanel bot={bot} limit={Number(limit)} />
			</TabsContent>
			<TabsContent value="indicators">
				<IndicatorsPanel bot={bot} limit={Number(limit)} />
			</TabsContent>
		</Tabs>
	);
}
