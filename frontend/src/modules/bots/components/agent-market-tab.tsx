import { useState } from 'react';
import type { Bot } from '@/modules/bots/api/bots.api';
import { CandleFeaturesTable } from '@/modules/features/components/candle-features-table';
import { IndicatorsGlossary } from '@/modules/features/components/indicators-glossary';
import { useCandleFeaturesQuery } from '@/modules/features/hooks/use-features-queries';
import { CandlesTable } from '@/modules/market/components/candles-table';
import { useCandlesQuery } from '@/modules/market/hooks/use-market-queries';
import { CANDLE_LIMIT_OPTIONS } from '@/modules/market/lib/market-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from '@/modules/ui/components/tabs';

// Velas e indicadores solo existen para el símbolo y timeframe de un agente
// activo (el scheduler los descarga y calcula por él), así que se muestran
// aquí, sin selectores.

function emptyMessage(bot: Bot, what: 'velas' | 'indicadores') {
	const isActive = bot.status === 'running' || bot.status === 'paused';
	return isActive
		? `Preparando ${what}. Suele tardar uno o dos minutos.`
		: `Aún no hay ${what}. Inicia el agente para que los descargue y calcule.`;
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

export function AgentMarketTab({ bot }: { bot: Bot }) {
	const [limit, setLimit] = useState('100');

	return (
		<Tabs defaultValue="candles" className="gap-3">
			<div className="flex flex-wrap items-center justify-between gap-3">
				<TabsList variant="line">
					<TabsTrigger value="candles">Velas</TabsTrigger>
					<TabsTrigger value="indicators">Indicadores</TabsTrigger>
				</TabsList>
				<OptionSelect
					aria-label="Cantidad de velas"
					size="sm"
					value={limit}
					onChange={(value) => setLimit(value ?? '100')}
					options={CANDLE_LIMIT_OPTIONS}
					className="w-36"
				/>
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
