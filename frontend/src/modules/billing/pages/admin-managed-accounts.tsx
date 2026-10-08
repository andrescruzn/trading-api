import { IconPencil, IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import { botLabel } from '@/modules/alerts/lib/alerts-labels';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { ManagedAccount } from '@/modules/billing/api/billing.api';
import { ManagedAccountFormDialog } from '@/modules/billing/components/managed-account-form-dialog';
import {
	useInvestorsQuery,
	useManagedAccountsQuery,
} from '@/modules/billing/hooks/use-billing-queries';
import { PERIOD_TYPE_LABELS } from '@/modules/billing/lib/billing-labels';
import { useBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { useSymbolsQuery } from '@/modules/market/hooks/use-market-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatPrice } from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';

const MONEY = 'text-right font-mono tabular-nums';

export function AdminManagedAccountsPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Cuentas gestionadas' }]);
	const managedAccountsQuery = useManagedAccountsQuery();
	const investorsQuery = useInvestorsQuery();
	const accountsQuery = useAccountsQuery();
	const botsQuery = useBotsQuery();
	const symbolsQuery = useSymbolsQuery();
	// `undefined` = diálogo cerrado; `null` = crear; una cuenta = editar.
	const [editing, setEditing] = useState<ManagedAccount | null | undefined>(undefined);

	function investorName(investorId: number) {
		const investor = investorsQuery.data?.find((item) => item.id === investorId);
		return investor
			? `#${investor.id} · usuario #${investor.user_id}`
			: `#${investorId}`;
	}

	function accountName(accountId: number) {
		return (
			accountsQuery.data?.find((item) => item.id === accountId)?.name ?? `#${accountId}`
		);
	}

	const columns: DataTableColumn<ManagedAccount>[] = [
		{
			id: 'name',
			header: 'Nombre',
			cell: (row) => <span className="font-medium">{row.name}</span>,
			skeletonClassName: 'w-36',
		},
		{ id: 'investor', header: 'Inversor', cell: (row) => investorName(row.investor_id) },
		{ id: 'account', header: 'Cuenta', cell: (row) => accountName(row.account_id) },
		{
			id: 'bot',
			header: 'Bot',
			cell: (row) =>
				row.bot_id ? (
					botLabel(row.bot_id, botsQuery.data, symbolsQuery.data)
				) : (
					<span className="text-muted-foreground">Sin bot</span>
				),
		},
		{
			id: 'capital',
			header: 'Capital inicial',
			className: MONEY,
			cell: (row) => formatPrice(row.initial_capital),
		},
		{
			id: 'hwm',
			header: 'Marca de agua (HWM)',
			className: MONEY,
			cell: (row) => formatPrice(row.high_water_mark),
		},
		{
			id: 'period',
			header: 'Facturación',
			cell: (row) => (
				<Badge variant="outline">
					{PERIOD_TYPE_LABELS[row.period_type] ?? row.period_type}
				</Badge>
			),
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => (
				<Badge variant={row.is_active ? 'secondary' : 'outline'}>
					{row.is_active ? 'Activa' : 'Inactiva'}
				</Badge>
			),
		},
		{
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) => (
				<Button variant="ghost" size="sm" onClick={() => setEditing(row)}>
					<IconPencil />
					Editar
				</Button>
			),
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Cuentas gestionadas"
				description="Cuentas de trading operadas en nombre de un inversor."
				actions={[
					{
						label: 'Nueva cuenta gestionada',
						icon: <IconPlus />,
						onClick: () => setEditing(null),
					},
				]}
			/>
			<DataTable
				columns={columns}
				rows={managedAccountsQuery.data}
				getRowId={(row) => row.id}
				isLoading={managedAccountsQuery.isLoading}
				error={managedAccountsQuery.error}
				errorTitle="No pudimos cargar las cuentas gestionadas"
				empty="Aún no hay cuentas gestionadas. Crea una para empezar a facturar a un inversor."
			/>
			<ManagedAccountFormDialog
				open={editing !== undefined}
				onOpenChange={(open) => !open && setEditing(undefined)}
				managedAccount={editing ?? null}
			/>
		</div>
	);
}
