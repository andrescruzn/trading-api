import { IconCircleCheck, IconLock, IconPlayerPlay } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { BillingPeriod } from '@/modules/billing/api/billing.api';
import {
	ClosePeriodDialog,
	OpenPeriodDialog,
} from '@/modules/billing/components/billing-period-dialogs';
import {
	BillingPeriodsTable,
	FeeTransactionsTable,
} from '@/modules/billing/components/billing-tables';
import {
	useBillingPeriodsQuery,
	useFeeTransactionsQuery,
	useManagedAccountsQuery,
} from '@/modules/billing/hooks/use-billing-queries';
import {
	managedAccountOptions,
	pnlClassName,
} from '@/modules/billing/lib/billing-labels';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatPrice, toNumber } from '@/modules/shared/lib/format';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Button } from '@/modules/ui/components/button';
import { Field, FieldDescription, FieldLabel } from '@/modules/ui/components/field';
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from '@/modules/ui/components/tabs';

export function AdminBillingPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Facturación' }]);
	const managedAccountsQuery = useManagedAccountsQuery();
	const [selectedId, setSelectedId] = useState<string | null>(null);
	const [isOpening, setIsOpening] = useState(false);
	const [closing, setClosing] = useState<BillingPeriod | null>(null);
	const [closedPeriod, setClosedPeriod] = useState<BillingPeriod | null>(null);

	const account =
		managedAccountsQuery.data?.find((item) => String(item.id) === selectedId) ?? null;
	const accountId = account?.id ?? null;
	const periodsQuery = useBillingPeriodsQuery(accountId);
	const feesQuery = useFeeTransactionsQuery(accountId);
	const hasOpenPeriod =
		periodsQuery.data?.some((period) => period.status === 'open') ?? false;

	function handleAccountChange(value: string | null) {
		setSelectedId(value);
		setClosedPeriod(null);
	}

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Facturación"
				description="Períodos de facturación y comisiones de desempeño de las cuentas gestionadas."
				actions={[
					{
						label: 'Abrir período',
						icon: <IconPlayerPlay />,
						onClick: () => setIsOpening(true),
						disabled: !account || hasOpenPeriod,
					},
				]}
			/>

			{managedAccountsQuery.error ? (
				<ErrorAlert
					title="No pudimos cargar las cuentas gestionadas"
					error={managedAccountsQuery.error}
				/>
			) : (
				<div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:gap-6">
					<Field className="sm:max-w-sm">
						<FieldLabel htmlFor="billing-account">Cuenta gestionada</FieldLabel>
						<OptionSelect
							id="billing-account"
							value={selectedId}
							onChange={handleAccountChange}
							options={managedAccountOptions(managedAccountsQuery.data)}
							placeholder={
								managedAccountsQuery.isLoading ? 'Cargando cuentas…' : 'Elige una cuenta'
							}
							disabled={managedAccountsQuery.isLoading}
						/>
						{hasOpenPeriod && (
							<FieldDescription>
								Esta cuenta tiene un período abierto: ciérralo para abrir uno nuevo.
							</FieldDescription>
						)}
					</Field>
					{account && (
						<dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm sm:pt-8">
							<dt className="text-muted-foreground">Marca de agua (HWM)</dt>
							<dd className="font-mono font-medium tabular-nums">
								{formatPrice(account.high_water_mark)}
							</dd>
							<dt className="text-muted-foreground">Capital inicial</dt>
							<dd className="font-mono tabular-nums">
								{formatPrice(account.initial_capital)}
							</dd>
						</dl>
					)}
				</div>
			)}

			{closedPeriod && closedPeriod.managed_account_id === accountId && (
				<Alert>
					<IconCircleCheck className="text-chart-1" />
					<AlertTitle>Período #{closedPeriod.id} cerrado</AlertTitle>
					<AlertDescription>
						<p>
							PnL bruto{' '}
							<span className={pnlClassName(closedPeriod.gross_pnl)}>
								{formatPrice(closedPeriod.gross_pnl)}
							</span>{' '}
							· Comisión {formatPrice(closedPeriod.fee_amount)} · PnL neto{' '}
							<span className={pnlClassName(closedPeriod.net_pnl)}>
								{formatPrice(closedPeriod.net_pnl)}
							</span>
							.
						</p>
						<p>
							{(toNumber(closedPeriod.fee_amount) ?? 0) > 0
								? 'La comisión quedó registrada como pendiente de cobro.'
								: 'No hubo ganancia por encima de la marca de agua: no se cobra comisión.'}
						</p>
					</AlertDescription>
				</Alert>
			)}

			{account ? (
				<Tabs defaultValue="periods">
					<TabsList>
						<TabsTrigger value="periods">Períodos</TabsTrigger>
						<TabsTrigger value="fees">Transacciones</TabsTrigger>
					</TabsList>
					<TabsContent value="periods" className="pt-2">
						<BillingPeriodsTable
							rows={periodsQuery.data}
							isLoading={periodsQuery.isLoading}
							error={periodsQuery.error}
							empty="Esta cuenta aún no tiene períodos. Abre el primero para empezar a facturar."
							renderActions={(period) =>
								period.status === 'open' ? (
									<Button variant="outline" size="sm" onClick={() => setClosing(period)}>
										<IconLock />
										Cerrar
									</Button>
								) : null
							}
						/>
					</TabsContent>
					<TabsContent value="fees" className="pt-2">
						<FeeTransactionsTable
							rows={feesQuery.data}
							isLoading={feesQuery.isLoading}
							error={feesQuery.error}
							empty="Aún no hay comisiones registradas para esta cuenta."
							showNotes
						/>
					</TabsContent>
				</Tabs>
			) : (
				<p className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
					Elige una cuenta gestionada para ver sus períodos y comisiones.
				</p>
			)}

			<OpenPeriodDialog
				open={isOpening}
				onOpenChange={setIsOpening}
				managedAccount={account}
			/>
			<ClosePeriodDialog
				period={closing}
				managedAccount={account}
				onOpenChange={(open) => !open && setClosing(null)}
				onClosed={setClosedPeriod}
			/>
		</div>
	);
}
