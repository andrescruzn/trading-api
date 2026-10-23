import { IconAlertTriangle, IconNetwork } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import { CopyText } from '@/modules/fund/components/copy-text';
import { DepositNetworksDialog } from '@/modules/fund/components/deposit-networks-dialog';
import { FundSettingsForm } from '@/modules/fund/components/fund-settings-form';
import { useFundSettingsQuery } from '@/modules/fund/hooks/use-fund-queries';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardAction,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { Skeleton } from '@/modules/ui/components/skeleton';

/** Ajustes del fondo: reglas y redes de depósito (el socio, en solo lectura). */
export function AdminFundSettingsPage() {
	usePageBreadcrumb([
		{ label: 'Administración' },
		{ label: 'Ajustes del fondo' },
	]);
	const canManage = useCanManage();
	const settingsQuery = useFundSettingsQuery();
	const [editingNetworks, setEditingNetworks] = useState(false);
	const settings = settingsQuery.data;

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Ajustes del fondo"
				description="Por dónde entra el dinero y las reglas que aplican a todos los participantes."
			/>
			{settingsQuery.error ? (
				<ErrorAlert
					title="No pudimos cargar los ajustes"
					error={settingsQuery.error}
				/>
			) : !settings ? (
				<Skeleton className="h-64 w-full" />
			) : (
				<>
					<Card>
						<CardHeader>
							<CardTitle>Redes de depósito</CardTitle>
							<CardDescription>
								Las direcciones que ven los participantes al depositar.
							</CardDescription>
							{canManage && (
								<CardAction>
									<Button
										variant="outline"
										size="sm"
										onClick={() => setEditingNetworks(true)}
									>
										<IconNetwork />
										Cambiar redes
									</Button>
								</CardAction>
							)}
						</CardHeader>
						<CardContent>
							{settings.deposit_networks.length === 0 ? (
								<Alert>
									<IconAlertTriangle />
									<AlertTitle>Aún no se puede depositar</AlertTitle>
									<AlertDescription>
										Elige al menos una red para que los participantes vean a
										dónde enviar el dinero.
									</AlertDescription>
								</Alert>
							) : (
								<ul className="flex flex-col gap-3">
									{settings.deposit_networks.map((network) => (
										<li
											key={network.network}
											className="flex flex-col gap-1 rounded-lg border p-3"
										>
											<span className="text-sm font-medium">
												{network.name}{' '}
												<span className="text-muted-foreground">
													({network.network})
												</span>
											</span>
											<CopyText value={network.address} label="Dirección" />
											{network.tag && (
												<span className="text-sm text-muted-foreground">
													Memo: <CopyText value={network.tag} label="Memo" />
												</span>
											)}
										</li>
									))}
								</ul>
							)}
						</CardContent>
					</Card>
					<FundSettingsForm settings={settings} readOnly={!canManage} />
					<DepositNetworksDialog
						open={editingNetworks}
						onOpenChange={setEditingNetworks}
						current={settings.deposit_networks}
					/>
				</>
			)}
		</div>
	);
}
