import { IconChartBar } from '@tabler/icons-react';
import { useState } from 'react';
import type { Account } from '@/modules/accounts/api/accounts.api';
import { AccountBalancesSheet } from '@/modules/accounts/components/account-balances-sheet';
import {
	AccountModeBadge,
	AccountStatusBadge,
	CredentialsIndicator,
} from '@/modules/accounts/components/account-badges';
import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import {
	ACCOUNT_MODE_LABELS,
	ACCOUNT_STATUS_OPTIONS,
} from '@/modules/accounts/lib/accounts-labels';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useExchangesQuery } from '@/modules/market/hooks/use-market-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDate } from '@/modules/shared/lib/format';
import { Button } from '@/modules/ui/components/button';

const ALL = 'all';

const MODE_FILTER_OPTIONS = [
	{ value: ALL, label: 'Todos los modos' },
	...Object.entries(ACCOUNT_MODE_LABELS).map(([value, label]) => ({ value, label })),
];

const STATUS_FILTER_OPTIONS = [
	{ value: ALL, label: 'Todos los estados' },
	...ACCOUNT_STATUS_OPTIONS,
];

export function AdminAccountsPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Cuentas' }]);
	const accountsQuery = useAccountsQuery();
	const exchangesQuery = useExchangesQuery();
	const [mode, setMode] = useState(ALL);
	const [status, setStatus] = useState(ALL);
	const [viewingBalances, setViewingBalances] = useState<Account | null>(null);

	// El endpoint no filtra: con pocas cuentas basta con hacerlo en el navegador.
	const accounts = accountsQuery.data?.filter(
		(account) =>
			(mode === ALL || account.mode === mode) &&
			(status === ALL || account.status === status),
	);
	const isFiltered = mode !== ALL || status !== ALL;

	const exchangeName = (id: number | null) =>
		id === null
			? '—'
			: (exchangesQuery.data?.find((exchange) => exchange.id === id)?.name ?? '—');

	const columns: DataTableColumn<Account>[] = [
		{ id: 'id', header: 'ID', className: 'w-16 font-mono', cell: (row) => row.id },
		{
			id: 'user',
			header: 'Usuario',
			className: 'font-mono',
			cell: (row) => `#${row.user_id}`,
		},
		{
			id: 'name',
			header: 'Nombre',
			cell: (row) => <span className="font-medium">{row.name}</span>,
		},
		{ id: 'exchange', header: 'Exchange', cell: (row) => exchangeName(row.exchange_id) },
		{ id: 'mode', header: 'Modo', cell: (row) => <AccountModeBadge mode={row.mode} /> },
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
		{ id: 'created', header: 'Creada', cell: (row) => formatDate(row.created_at) },
		{
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) => (
				<Button variant="ghost" size="sm" onClick={() => setViewingBalances(row)}>
					<IconChartBar />
					Ver balances
				</Button>
			),
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Cuentas"
				description="Todas las cuentas del sistema, de todos los usuarios. Solo lectura."
			/>
			<div className="grid gap-3 sm:grid-cols-2 lg:max-w-xl">
				<OptionSelect
					aria-label="Modo"
					size="sm"
					value={mode}
					onChange={(value) => setMode(value ?? ALL)}
					options={MODE_FILTER_OPTIONS}
				/>
				<OptionSelect
					aria-label="Estado"
					size="sm"
					value={status}
					onChange={(value) => setStatus(value ?? ALL)}
					options={STATUS_FILTER_OPTIONS}
				/>
			</div>
			<DataTable
				columns={columns}
				rows={accounts}
				getRowId={(row) => row.id}
				isLoading={accountsQuery.isLoading}
				error={accountsQuery.error}
				errorTitle="No pudimos cargar las cuentas"
				empty={
					isFiltered
						? 'No hay cuentas con esos filtros.'
						: 'Aún no hay cuentas en el sistema.'
				}
			/>
			<AccountBalancesSheet
				account={viewingBalances}
				onClose={() => setViewingBalances(null)}
				canRecord={false}
			/>
		</div>
	);
}
