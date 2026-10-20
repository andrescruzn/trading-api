import { IconDownload } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import {
	BillingPeriodsTable,
	FeeTransactionsTable,
} from '@/modules/billing/components/billing-tables';
import { CapitalMovementsTable } from '@/modules/billing/components/capital-movements-table';
import {
	useBillingPeriodsQuery,
	useCapitalMovementsQuery,
	useFeeTransactionsQuery,
	useInvestorsQuery,
	useManagedAccountsQuery,
} from '@/modules/billing/hooks/use-billing-queries';
import {
	managedAccountOptions,
	PERIOD_TYPE_LABELS,
	pnlClassName,
	sumClosedPeriods,
} from '@/modules/billing/lib/billing-labels';
import {
	buildStatementCsv,
	downloadCsv,
} from '@/modules/billing/lib/billing-statement';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { StatCard } from '@/modules/shared/components/stat-card';
import {
	formatPercent,
	formatPrice,
	toNumber,
} from '@/modules/shared/lib/format';
import { Button } from '@/modules/ui/components/button';
import { Field, FieldLabel } from '@/modules/ui/components/field';

const STAT_LABELS = [
	'Capital inicial',
	'Marca de agua (HWM)',
	'PnL neto',
	'Comisiones pagadas',
	'Comisión de desempeño',
];

function EmptyState({ children }: { children: string }) {
	return (
		<p className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
			{children}
		</p>
	);
}

export function InvestorDashboardPage() {
	usePageBreadcrumb([{ label: 'Inversor' }, { label: 'Mi inversión' }]);
	const { user } = useAuth();
	const investorsQuery = useInvestorsQuery();
	const accountsQuery = useManagedAccountsQuery();
	const [selectedId, setSelectedId] = useState<string | null>(null);

	// El backend ya devuelve solo el perfil propio; se cruza por usuario por si acaso.
	const investor = investorsQuery.data?.find(
		(item) => item.user_id === user?.id,
	);
	const accounts = accountsQuery.data ?? [];
	// Con una sola cuenta se muestra directamente, sin obligar a elegirla.
	const effectiveId =
		selectedId ?? (accounts.length === 1 ? String(accounts[0]?.id) : null);
	const account = accounts.find((item) => String(item.id) === effectiveId);
	const accountId = account?.id ?? null;

	const periodsQuery = useBillingPeriodsQuery(accountId);
	const movementsQuery = useCapitalMovementsQuery(accountId);
	const feesQuery = useFeeTransactionsQuery(accountId);

	const totalNetPnl = sumClosedPeriods(periodsQuery.data, 'net_pnl');
	// Comisiones por estado real (no todas las de un período cerrado se cobraron)
	const fees = feesQuery.data ?? [];
	const sumFees = (status: string) =>
		fees
			.filter((fee) => fee.status === status)
			.reduce((total, fee) => total + (toNumber(fee.amount) ?? 0), 0);
	const chargedFees = sumFees('charged');
	const pendingFees = sumFees('pending');

	function downloadStatement() {
		if (!account) return;
		downloadCsv(
			`extracto-${account.name.toLowerCase().replaceAll(/[^a-z0-9]+/g, '-')}.csv`,
			buildStatementCsv(
				account,
				periodsQuery.data ?? [],
				fees,
				movementsQuery.data?.movements ?? [],
			),
		);
	}
	const isLoadingProfile = investorsQuery.isLoading || accountsQuery.isLoading;
	const loadError = investorsQuery.error ?? accountsQuery.error;

	function renderContent() {
		if (loadError) {
			return (
				<ErrorAlert title="No pudimos cargar tu inversión" error={loadError} />
			);
		}
		if (isLoadingProfile) {
			return (
				<div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
					{STAT_LABELS.map((label) => (
						<StatCard key={label} label={label} value="" isLoading />
					))}
				</div>
			);
		}
		if (!investor) {
			return (
				<EmptyState>
					Aún no tienes un perfil de inversor. Pide a un administrador que lo
					cree para ver tu inversión aquí.
				</EmptyState>
			);
		}
		if (accounts.length === 0) {
			return (
				<EmptyState>
					Aún no tienes cuentas gestionadas. Cuando un administrador te asigne
					una, verás aquí su rendimiento y tus comisiones.
				</EmptyState>
			);
		}

		return (
			<>
				<Field className="sm:max-w-sm">
					<FieldLabel htmlFor="investor-account">Cuenta gestionada</FieldLabel>
					<OptionSelect
						id="investor-account"
						value={effectiveId}
						onChange={setSelectedId}
						options={managedAccountOptions(accounts)}
						placeholder="Elige una cuenta"
					/>
				</Field>

				{account ? (
					<>
						<div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
							<StatCard
								label="Capital inicial"
								value={formatPrice(account.initial_capital)}
								hint={`Facturación ${PERIOD_TYPE_LABELS[account.period_type]?.toLowerCase() ?? ''}`}
							/>
							<StatCard
								label="Marca de agua (HWM)"
								value={formatPrice(account.high_water_mark)}
								hint="Máximo histórico de la cuenta"
							/>
							<StatCard
								label="PnL neto"
								value={
									<span className={pnlClassName(totalNetPnl)}>
										{formatPrice(totalNetPnl)}
									</span>
								}
								hint="Períodos cerrados, ya descontada la comisión"
								isLoading={periodsQuery.isLoading}
							/>
							<StatCard
								label="Comisiones pagadas"
								value={formatPrice(chargedFees)}
								hint={
									pendingFees > 0
										? `${formatPrice(pendingFees)} pendientes de cobro`
										: 'Sin comisiones pendientes'
								}
								isLoading={feesQuery.isLoading}
							/>
							<StatCard
								label="Comisión de desempeño"
								value={formatPercent(investor.fee_pct)}
								hint="Sobre la ganancia por encima de la marca de agua"
							/>
						</div>

						<section className="flex flex-col gap-3">
							<div className="flex flex-wrap items-center justify-between gap-2">
								<h2 className="text-base font-semibold">
									Períodos de facturación
								</h2>
								<Button
									size="sm"
									variant="outline"
									onClick={downloadStatement}
									disabled={!periodsQuery.data?.length}
								>
									<IconDownload />
									Descargar extracto (CSV)
								</Button>
							</div>
							<BillingPeriodsTable
								rows={periodsQuery.data}
								isLoading={periodsQuery.isLoading}
								error={periodsQuery.error}
								empty="Aún no hay períodos de facturación para esta cuenta."
							/>
						</section>

						<section className="flex flex-col gap-3">
							<h2 className="text-base font-semibold">
								Comisiones de desempeño
							</h2>
							<FeeTransactionsTable
								rows={feesQuery.data}
								isLoading={feesQuery.isLoading}
								error={feesQuery.error}
								empty="Aún no se te ha cobrado ninguna comisión en esta cuenta."
							/>
						</section>

						<section className="flex flex-col gap-3">
							<h2 className="text-base font-semibold">Aportes y retiros</h2>
							<p className="text-sm text-muted-foreground">
								El dinero que aportas o retiras ajusta la marca de agua: la
								comisión solo se cobra sobre la ganancia, nunca sobre tus
								depósitos.
							</p>
							<CapitalMovementsTable
								rows={movementsQuery.data?.movements}
								isLoading={movementsQuery.isLoading}
								error={movementsQuery.error}
								empty="Aún no hay aportes ni retiros en esta cuenta."
							/>
						</section>
					</>
				) : (
					<EmptyState>
						Elige una cuenta gestionada para ver su rendimiento.
					</EmptyState>
				)}
			</>
		);
	}

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Mi inversión"
				description="Rendimiento, PnL y comisiones de tu capital en cuentas gestionadas."
			/>
			{renderContent()}
		</div>
	);
}
