import { IconAlertTriangle, IconLoader2 } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import type { Account } from '@/modules/accounts/api/accounts.api';
import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import { useSetPlatformWalletMutation } from '@/modules/accounts/hooks/use-wallet-mutations';
import { ACCOUNT_MODE_LABELS } from '@/modules/accounts/lib/accounts-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Button } from '@/modules/ui/components/button';
import {
	Dialog,
	DialogBody,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from '@/modules/ui/components/dialog';
import {
	Field,
	FieldDescription,
	FieldLabel,
} from '@/modules/ui/components/field';
import { toast } from '@/modules/ui/components/toast';

type WalletAccountDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	/** Cuenta que hoy es la billetera (para preseleccionarla). */
	currentAccountId: number | null;
};

/** Sirve como billetera: activa, con exchange y, si es live, con API key. */
function isEligible(account: Account) {
	return (
		account.status === 'active' &&
		account.exchange_id !== null &&
		(account.mode === 'paper' || account.has_credentials)
	);
}

/** Un super admin elige qué cuenta de Binance guarda el dinero del fondo. */
export function WalletAccountDialog({
	open,
	onOpenChange,
	currentAccountId,
}: WalletAccountDialogProps) {
	const accountsQuery = useAccountsQuery();
	const setMutation = useSetPlatformWalletMutation();
	const [accountId, setAccountId] = useState<string | null>(null);

	useEffect(() => {
		if (open) setAccountId(currentAccountId ? String(currentAccountId) : null);
	}, [open, currentAccountId]);

	const eligible = (accountsQuery.data ?? []).filter(isEligible);
	const options = eligible.map((account) => ({
		value: String(account.id),
		label: `${account.name} · ${ACCOUNT_MODE_LABELS[account.mode]}`,
	}));
	const selected = eligible.find((account) => String(account.id) === accountId);
	const changing =
		currentAccountId !== null &&
		!!accountId &&
		Number(accountId) !== currentAccountId;

	function save() {
		if (!accountId) return;
		setMutation.mutate(Number(accountId), {
			onSuccess: () => {
				toast.add({
					title: 'Billetera guardada',
					description: 'Sincronízala para ver su saldo.',
					type: 'success',
				});
				onOpenChange(false);
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos guardar la billetera',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Billetera de la plataforma</DialogTitle>
					<DialogDescription>
						La cuenta de exchange que guarda el dinero de todos: propietarios,
						socios e inversores. Toda la plataforma usa una sola.
					</DialogDescription>
				</DialogHeader>
				<DialogBody>
					<div className="flex flex-col gap-4">
						<Field>
							<FieldLabel htmlFor="wallet-account" required>
								Cuenta
							</FieldLabel>
							<OptionSelect
								id="wallet-account"
								value={accountId}
								onChange={setAccountId}
								options={options}
								placeholder={
									accountsQuery.isLoading
										? 'Cargando cuentas…'
										: 'Elige una cuenta'
								}
								disabled={accountsQuery.isLoading || options.length === 0}
							/>
							<FieldDescription>
								{options.length === 0 && !accountsQuery.isLoading
									? 'No hay cuentas que sirvan: debe estar activa, tener exchange y, si es live, su API key. Créala en Mis cuentas.'
									: 'Para una cuenta live usa una API key con permiso de lectura y sin permiso de retiro: los retiros los hacen ustedes desde el exchange.'}
							</FieldDescription>
						</Field>
						{selected?.mode === 'paper' && (
							<Alert>
								<IconAlertTriangle />
								<AlertTitle>Cuenta de práctica</AlertTitle>
								<AlertDescription>
									Su saldo es el que registres a mano en Mis cuentas. Úsala solo
									para probar: el dinero real va en una cuenta live.
								</AlertDescription>
							</Alert>
						)}
						{changing && (
							<Alert variant="destructive">
								<IconAlertTriangle />
								<AlertTitle>Vas a cambiar de billetera</AlertTitle>
								<AlertDescription>
									El saldo y la conciliación pasan a leerse de la cuenta nueva.
									Hazlo solo después de mover el dinero entre las dos cuentas.
								</AlertDescription>
							</Alert>
						)}
					</div>
				</DialogBody>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button
						onClick={save}
						disabled={
							!accountId ||
							setMutation.isPending ||
							Number(accountId) === currentAccountId
						}
					>
						{setMutation.isPending && <IconLoader2 className="animate-spin" />}
						Guardar billetera
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
