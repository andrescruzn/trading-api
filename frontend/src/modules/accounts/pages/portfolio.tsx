import {
	IconChartBar,
	IconDots,
	IconPencil,
	IconPlus,
} from '@tabler/icons-react';
import { useState } from 'react';
import type { Account } from '@/modules/accounts/api/accounts.api';
import {
	AccountModeBadge,
	AccountStatusBadge,
	CredentialsIndicator,
} from '@/modules/accounts/components/account-badges';
import { AccountBalancesSheet } from '@/modules/accounts/components/account-balances-sheet';
import { AccountFormDialog } from '@/modules/accounts/components/account-form-dialog';
import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import { useExchangesQuery } from '@/modules/market/hooks/use-market-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDate } from '@/modules/shared/lib/format';
import { Button } from '@/modules/ui/components/button';
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
} from '@/modules/ui/components/dropdown-menu';

export function PortfolioPage() {
	usePageBreadcrumb([{ label: 'Trading' }, { label: 'Mis cuentas' }]);
	const { user } = useAuth();
	const accountsQuery = useAccountsQuery();
	const exchangesQuery = useExchangesQuery();
	// `undefined` = diálogo cerrado; `null` = crear; una cuenta = editar.
	const [editing, setEditing] = useState<Account | null | undefined>(undefined);
	const [viewingBalances, setViewingBalances] = useState<Account | null>(null);

	// Para un admin `GET /accounts` trae todas las cuentas del sistema: aquí solo
	// se muestran las propias (las demás están en Administración → Cuentas).
	const accounts = user
		? accountsQuery.data?.filter((account) => account.user_id === user.id)
		: accountsQuery.data;

	const exchangeName = (id: number | null) =>
		id === null
			? '—'
			: (exchangesQuery.data?.find((exchange) => exchange.id === id)?.name ??
				'—');

	const columns: DataTableColumn<Account>[] = [
		{
			id: 'name',
			header: 'Nombre',
			cell: (row) => <span className="font-medium">{row.name}</span>,
		},
		{
			id: 'exchange',
			header: 'Exchange',
			cell: (row) => exchangeName(row.exchange_id),
		},
		{
			id: 'mode',
			header: 'Modo',
			cell: (row) => <AccountModeBadge mode={row.mode} />,
		},
		{
			id: 'currency',
			header: 'Moneda base',
			cell: (row) => <span className="font-mono">{row.base_currency}</span>,
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => <AccountStatusBadge status={row.status} />,
		},
		{
			id: 'credentials',
			header: 'Credenciales',
			className: 'text-center',
			cell: (row) => <CredentialsIndicator account={row} />,
		},
		{
			id: 'created',
			header: 'Creada',
			cell: (row) => formatDate(row.created_at),
		},
		{
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) => (
				<DropdownMenu>
					<DropdownMenuTrigger
						render={<Button variant="ghost" size="icon-sm" />}
					>
						<IconDots />
						<span className="sr-only">Acciones de {row.name}</span>
					</DropdownMenuTrigger>
					<DropdownMenuContent align="end" className="w-auto min-w-44">
						<DropdownMenuItem onClick={() => setEditing(row)}>
							<IconPencil />
							Editar
						</DropdownMenuItem>
						<DropdownMenuItem onClick={() => setViewingBalances(row)}>
							<IconChartBar />
							Ver balances
						</DropdownMenuItem>
					</DropdownMenuContent>
				</DropdownMenu>
			),
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Mis cuentas"
				description="Cuentas de exchange en modo paper (simulado) o live (dinero real), con sus balances."
				actions={[
					{
						label: 'Nueva cuenta',
						icon: <IconPlus />,
						onClick: () => setEditing(null),
					},
				]}
			/>
			<DataTable
				columns={columns}
				rows={accounts}
				getRowId={(row) => row.id}
				isLoading={accountsQuery.isLoading}
				error={accountsQuery.error}
				errorTitle="No pudimos cargar tus cuentas"
				empty={
					<div className="flex flex-col items-center gap-3">
						<span>
							Aún no tienes cuentas. Crea una en modo paper para probar tus
							estrategias sin dinero real.
						</span>
						<Button size="sm" onClick={() => setEditing(null)}>
							<IconPlus />
							Nueva cuenta
						</Button>
					</div>
				}
			/>
			<AccountFormDialog
				open={editing !== undefined}
				onOpenChange={(open) => !open && setEditing(undefined)}
				account={editing ?? null}
			/>
			<AccountBalancesSheet
				account={viewingBalances}
				onClose={() => setViewingBalances(null)}
			/>
		</div>
	);
}
