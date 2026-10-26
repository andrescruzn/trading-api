import {
	IconAlertTriangle,
	IconCash,
	IconClock,
	IconLock,
	IconRefresh,
	IconWallet,
} from '@tabler/icons-react';
import type {
	WalletAssetLine,
	WalletSnapshot,
} from '@/modules/accounts/api/wallet.api';
import { useSyncWalletMutation } from '@/modules/accounts/hooks/use-wallet-mutations';
import {
	useWalletQuery,
	useWalletSnapshotsQuery,
} from '@/modules/accounts/hooks/use-wallet-queries';
import { WALLET_SOURCE_LABELS } from '@/modules/accounts/lib/accounts-labels';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { StatCard } from '@/modules/shared/components/stat-card';
import {
	formatDateTime,
	formatNumber,
	formatPrice,
} from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { toast } from '@/modules/ui/components/toast';

const ASSET_COLUMNS: DataTableColumn<WalletAssetLine>[] = [
	{
		id: 'asset',
		header: 'Activo',
		cell: (row) => <span className="font-mono font-medium">{row.asset}</span>,
	},
	{
		id: 'free',
		header: 'Libre',
		className: 'text-right tabular-nums',
		cell: (row) => formatNumber(row.free),
	},
	{
		id: 'locked',
		header: 'En órdenes',
		className: 'text-right tabular-nums',
		cell: (row) => formatNumber(row.locked),
	},
	{
		id: 'total',
		header: 'Total',
		className: 'text-right tabular-nums',
		cell: (row) => formatNumber(row.total),
	},
	{
		id: 'price',
		header: 'Precio',
		className: 'text-right tabular-nums',
		cell: (row) =>
			row.price === null ? (
				<span className="text-muted-foreground">Sin precio</span>
			) : (
				formatPrice(row.price)
			),
	},
	{
		id: 'value',
		header: 'Valor',
		className: 'text-right tabular-nums font-medium',
		cell: (row) => formatPrice(row.value),
	},
];

const HISTORY_COLUMNS: DataTableColumn<WalletSnapshot>[] = [
	{
		id: 'ts',
		header: 'Fecha',
		className: 'whitespace-nowrap',
		cell: (row) => formatDateTime(row.ts),
	},
	{
		id: 'total',
		header: 'Saldo total',
		className: 'text-right tabular-nums font-medium',
		cell: (row) => formatPrice(row.total_value),
	},
	{
		id: 'free',
		header: 'Libre',
		className: 'text-right tabular-nums',
		cell: (row) => formatPrice(row.free_value),
	},
	{
		id: 'locked',
		header: 'En órdenes',
		className: 'text-right tabular-nums',
		cell: (row) => formatPrice(row.locked_value),
	},
	{
		id: 'source',
		header: 'Origen',
		cell: (row) => WALLET_SOURCE_LABELS[row.source] ?? row.source,
	},
];

export function AdminWalletPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Billetera' }]);
	const canManage = useCanManage();
	const walletQuery = useWalletQuery();
	const historyQuery = useWalletSnapshotsQuery();
	const syncMutation = useSyncWalletMutation();

	const overview = walletQuery.data;
	const wallet = overview?.wallet ?? null;
	const account = overview?.account ?? null;
	const snapshot = overview?.latest_snapshot ?? null;
	const base = wallet?.base_asset ?? 'USDT';

	function sync() {
		syncMutation.mutate(undefined, {
			onSuccess: () =>
				toast.add({ title: 'Saldo actualizado', type: 'success' }),
			onError: (error) =>
				toast.add({
					title: 'No pudimos leer el saldo',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Billetera de Binance"
				description="El saldo de la billetera de Binance que guarda el dinero de todos. Es la única de la plataforma y se lee sola cada pocos minutos. Solo la ven los super admin y los socios."
				actions={[
					{
						label: syncMutation.isPending
							? 'Sincronizando…'
							: 'Sincronizar ahora',
						icon: <IconRefresh />,
						onClick: sync,
						disabled: !overview?.configured || syncMutation.isPending,
						hidden: !canManage,
					},
				]}
			/>

			{walletQuery.error ? (
				<ErrorAlert
					title="No pudimos cargar la billetera"
					error={walletQuery.error}
				/>
			) : overview && !overview.configured ? (
				<Card>
					<CardHeader>
						<CardTitle>La billetera de Binance aún no está conectada</CardTitle>
						<CardDescription>
							Faltan la API key y el secret de Binance en el servidor. Sin ellos
							no podemos leer el saldo ni operar los agentes reales.
						</CardDescription>
					</CardHeader>
					<CardContent className="text-sm text-muted-foreground">
						Quien administra el servidor debe poner{' '}
						<code className="font-mono text-foreground">BINANCE_API_KEY</code> y{' '}
						<code className="font-mono text-foreground">
							BINANCE_API_SECRET
						</code>{' '}
						en el archivo <code className="font-mono">.env</code> (con permiso
						de lectura y trading, nunca de retiro) y reiniciar la API.
					</CardContent>
				</Card>
			) : (
				<>
					{account && (
						<div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
							<span className="font-medium text-foreground">
								{account.name}
							</span>
							<span aria-hidden>·</span>
							<span>Binance</span>
						</div>
					)}

					{wallet?.last_sync_error && (
						<Alert variant="destructive">
							<IconAlertTriangle />
							<AlertTitle>La última sincronización falló</AlertTitle>
							<AlertDescription>
								{wallet.last_sync_error_msg}{' '}
								{snapshot
									? 'Abajo ves el último saldo que sí se pudo leer.'
									: ''}
							</AlertDescription>
						</Alert>
					)}

					{snapshot && snapshot.missing_prices.length > 0 && (
						<Alert>
							<IconAlertTriangle />
							<AlertTitle>El total no incluye todos los activos</AlertTitle>
							<AlertDescription>
								No encontramos precio en {base} para{' '}
								{snapshot.missing_prices.join(', ')}: no suman al saldo total.
							</AlertDescription>
						</Alert>
					)}

					<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
						<StatCard
							label="Saldo total"
							value={snapshot ? formatPrice(snapshot.total_value) : '—'}
							hint={`En ${base}, libre + en órdenes`}
							icon={<IconWallet className="size-4" />}
							isLoading={walletQuery.isLoading}
						/>
						<StatCard
							label="Saldo libre"
							value={snapshot ? formatPrice(snapshot.free_value) : '—'}
							hint="Disponible para nuevas operaciones"
							icon={<IconCash className="size-4" />}
							isLoading={walletQuery.isLoading}
						/>
						<StatCard
							label="En órdenes"
							value={snapshot ? formatPrice(snapshot.locked_value) : '—'}
							hint="Bloqueado en órdenes abiertas del exchange"
							icon={<IconLock className="size-4" />}
							isLoading={walletQuery.isLoading}
						/>
						<StatCard
							label="Última lectura"
							value={snapshot ? formatDateTime(snapshot.ts) : 'Nunca'}
							hint={
								snapshot
									? WALLET_SOURCE_LABELS[snapshot.source]
									: 'Sincronízala para ver su saldo'
							}
							icon={<IconClock className="size-4" />}
							isLoading={walletQuery.isLoading}
						/>
					</div>

					<section className="flex flex-col gap-3">
						<h2 className="text-lg font-semibold tracking-tight">
							Activos en la billetera
						</h2>
						<DataTable
							columns={ASSET_COLUMNS}
							rows={
								snapshot?.assets ?? (walletQuery.isLoading ? undefined : [])
							}
							getRowId={(row) => row.asset}
							isLoading={walletQuery.isLoading}
							errorTitle="No pudimos cargar los activos"
							empty="La billetera no tiene saldo."
						/>
					</section>

					<section className="flex flex-col gap-3">
						<h2 className="text-lg font-semibold tracking-tight">
							Historial de saldo
						</h2>
						<DataTable
							columns={HISTORY_COLUMNS}
							rows={historyQuery.data}
							getRowId={(row) => row.id}
							isLoading={historyQuery.isLoading}
							error={historyQuery.error}
							errorTitle="No pudimos cargar el historial"
							empty="Aún no hay lecturas del saldo."
						/>
					</section>
				</>
			)}
		</div>
	);
}
