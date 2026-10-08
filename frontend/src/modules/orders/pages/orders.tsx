import { IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { BotModeBadge, BotStatusBadge } from '@/modules/bots/components/bot-badges';
import { useBotCatalogs } from '@/modules/bots/hooks/use-bot-catalogs';
import { useBotsByAccountsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { BOT_MODE_LABELS, describeBot } from '@/modules/bots/lib/bots-labels';
import type { Order } from '@/modules/orders/api/orders.api';
import { FillsTable } from '@/modules/orders/components/fills-table';
import { OrderFillsDialog } from '@/modules/orders/components/order-fills-dialog';
import { OrderFormDialog } from '@/modules/orders/components/order-form-dialog';
import { OrdersTable } from '@/modules/orders/components/orders-table';
import { PositionsGrid } from '@/modules/orders/components/positions-grid';
import {
	useBotFillsQuery,
	useBotOrdersQuery,
	useBotPositionsQuery,
} from '@/modules/orders/hooks/use-orders-queries';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { Field, FieldLabel } from '@/modules/ui/components/field';
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from '@/modules/ui/components/tabs';

// Cada pestaña es su propio componente: Base UI desmonta los paneles
// inactivos, así que cada lista se pide solo al abrir su pestaña.

function OrdersTab({ botId }: { botId: number }) {
	const ordersQuery = useBotOrdersQuery(botId);
	const [fillsOrder, setFillsOrder] = useState<Order | null>(null);

	return (
		<>
			<OrdersTable
				orders={ordersQuery.data}
				isLoading={ordersQuery.isLoading}
				error={ordersQuery.error}
				empty="Este bot aún no tiene órdenes."
				onViewFills={setFillsOrder}
			/>
			<OrderFillsDialog
				order={fillsOrder}
				onOpenChange={(open) => !open && setFillsOrder(null)}
			/>
		</>
	);
}

function PositionsTab({
	botId,
	symbolNames,
}: {
	botId: number;
	symbolNames: Map<number, string>;
}) {
	const positionsQuery = useBotPositionsQuery(botId);
	return (
		<PositionsGrid
			positions={positionsQuery.data}
			isLoading={positionsQuery.isLoading}
			error={positionsQuery.error}
			symbolNames={symbolNames}
		/>
	);
}

function FillsTab({ botId }: { botId: number }) {
	const fillsQuery = useBotFillsQuery(botId);
	return (
		<FillsTable
			fills={fillsQuery.data}
			isLoading={fillsQuery.isLoading}
			error={fillsQuery.error}
			empty="Este bot aún no tiene ejecuciones."
		/>
	);
}

export function OrdersPage() {
	usePageBreadcrumb([{ label: 'Trading' }, { label: 'Órdenes' }]);
	const { accountsQuery, catalogs } = useBotCatalogs();
	const accountIds = (accountsQuery.data ?? []).map((account) => account.id);
	const botsQuery = useBotsByAccountsQuery(accountIds);
	const [pickedBotId, setPickedBotId] = useState<number | null>(null);
	const [creating, setCreating] = useState(false);

	const bots = botsQuery.data ?? [];
	// Sin elección explícita se muestra el bot más reciente.
	const selectedBot =
		bots.find((bot) => bot.id === pickedBotId) ?? (pickedBotId ? null : bots[0] ?? null);
	const selectedLabel = selectedBot ? describeBot(selectedBot, catalogs) : '';

	const botOptions = bots.map((bot) => ({
		value: String(bot.id),
		label: `${describeBot(bot, catalogs)} · ${BOT_MODE_LABELS[bot.mode] ?? bot.mode}`,
	}));

	const isLoadingBots = accountsQuery.isLoading || botsQuery.isLoading;
	const botsError = accountsQuery.error ?? botsQuery.error;

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Órdenes"
				description="Órdenes, posiciones y ejecuciones de tus bots."
				actions={[
					{
						label: 'Nueva orden',
						icon: <IconPlus />,
						onClick: () => setCreating(true),
						disabled: !selectedBot,
					},
				]}
			/>

			{botsError ? (
				<ErrorAlert title="No pudimos cargar tus bots" error={botsError} />
			) : (
				<div className="flex flex-col gap-3 sm:flex-row sm:items-end">
					<Field className="sm:max-w-md">
						<FieldLabel htmlFor="orders-bot">Bot</FieldLabel>
						<OptionSelect
							id="orders-bot"
							size="sm"
							value={selectedBot ? String(selectedBot.id) : null}
							onChange={(value) => setPickedBotId(value ? Number(value) : null)}
							options={botOptions}
							placeholder={isLoadingBots ? 'Cargando bots…' : 'Elige un bot'}
							disabled={isLoadingBots || bots.length === 0}
						/>
					</Field>
					{selectedBot && (
						<div className="flex items-center gap-2 sm:pb-2">
							<BotStatusBadge status={selectedBot.status} />
							<BotModeBadge mode={selectedBot.mode} />
						</div>
					)}
				</div>
			)}

			{selectedBot ? (
				<Tabs defaultValue="orders">
					<TabsList>
						<TabsTrigger value="orders">Órdenes</TabsTrigger>
						<TabsTrigger value="positions">Posiciones</TabsTrigger>
						<TabsTrigger value="fills">Ejecuciones</TabsTrigger>
					</TabsList>
					<TabsContent value="orders" className="pt-2">
						<OrdersTab botId={selectedBot.id} />
					</TabsContent>
					<TabsContent value="positions" className="pt-2">
						<PositionsTab botId={selectedBot.id} symbolNames={catalogs.symbols} />
					</TabsContent>
					<TabsContent value="fills" className="pt-2">
						<FillsTab botId={selectedBot.id} />
					</TabsContent>
				</Tabs>
			) : (
				!isLoadingBots &&
				!botsError && (
					<p className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
						{bots.length === 0
							? 'Aún no tienes bots. Crea uno en Bots para poder enviar órdenes.'
							: 'Elige un bot para ver sus órdenes.'}
					</p>
				)
			)}

			<OrderFormDialog
				open={creating}
				onOpenChange={setCreating}
				bot={selectedBot}
				botLabel={selectedLabel}
			/>
		</div>
	);
}
