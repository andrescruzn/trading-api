import { IconSearch } from '@tabler/icons-react';
import { useState } from 'react';
import { ChoiceCard } from '@/modules/bots/components/agent-wizard/choice-card';
import type { MarketSymbol } from '@/modules/market/api/market.api';
import { ASSET_CLASS_LABELS } from '@/modules/market/lib/market-labels';
import {
	InputGroup,
	InputGroupAddon,
	InputGroupInput,
} from '@/modules/ui/components/input-group';
import { Skeleton } from '@/modules/ui/components/skeleton';

type SymbolStepProps = {
	symbols: MarketSymbol[] | undefined;
	isLoading: boolean;
	value: string | null;
	onChange: (value: string) => void;
};

/** Paso 1: qué va a operar el agente. Solo símbolos con velas automáticas. */
export function SymbolStep({
	symbols,
	isLoading,
	value,
	onChange,
}: SymbolStepProps) {
	const [search, setSearch] = useState('');
	const term = search.trim().toLowerCase();
	const visible = (symbols ?? []).filter(
		(symbol) =>
			!term ||
			symbol.symbol.toLowerCase().includes(term) ||
			(symbol.exchange_name ?? '').toLowerCase().includes(term),
	);

	return (
		<div className="flex flex-col gap-4">
			<InputGroup className="sm:max-w-sm">
				<InputGroupAddon>
					<IconSearch />
				</InputGroupAddon>
				<InputGroupInput
					value={search}
					onChange={(event) => setSearch(event.target.value)}
					placeholder="Busca BTC, ETH, Binance…"
					aria-label="Buscar símbolo"
				/>
			</InputGroup>

			{isLoading ? (
				<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
					{Array.from({ length: 8 }, (_, index) => (
						<Skeleton key={index} className="h-20 rounded-xl" />
					))}
				</div>
			) : visible.length === 0 ? (
				<p className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">
					{term
						? 'No hay símbolos que coincidan con tu búsqueda.'
						: 'No hay símbolos disponibles. Un administrador debe activar alguno.'}
				</p>
			) : (
				<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
					{visible.map((symbol) => (
						<ChoiceCard
							key={symbol.id}
							selected={value === String(symbol.id)}
							onSelect={() => onChange(String(symbol.id))}
							eyebrow={[
								ASSET_CLASS_LABELS[symbol.asset_class] ?? symbol.asset_class,
								symbol.exchange_name,
							]
								.filter(Boolean)
								.join(' · ')}
							title={<span className="font-mono">{symbol.symbol}</span>}
						/>
					))}
				</div>
			)}
		</div>
	);
}
