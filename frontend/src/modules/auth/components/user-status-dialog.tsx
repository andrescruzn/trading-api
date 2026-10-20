import { IconAlertTriangle, IconLoader2 } from '@tabler/icons-react';
import { useState } from 'react';
import { useUpdateUserStatusMutation } from '@/modules/auth/hooks/use-users-mutations';
import { userDisplayName } from '@/modules/auth/hooks/use-users-queries';
import {
	USER_STATUS_ACTION_LABELS,
	type UserStatus,
	type UserStatusChange,
} from '@/modules/auth/lib/user-status';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from '@/modules/ui/components/alert-dialog';
import { toast } from '@/modules/ui/components/toast';

type UserStatusDialogProps = {
	/** `null` = cerrado. */
	change: UserStatusChange | null;
	onOpenChange: (open: boolean) => void;
};

const COPY: Record<
	UserStatus,
	{
		title: (name: string) => string;
		description: string;
		toastTitle: string;
		toastDescription: (name: string) => string;
	}
> = {
	blocked: {
		title: (name) => `¿Bloquear la cuenta de ${name}?`,
		description:
			'Úsalo para suspenderla por un tiempo, por ejemplo si ves actividad sospechosa. Cerramos su sesión ahora mismo y no podrá entrar hasta que vuelvas a activarla.',
		toastTitle: 'Cuenta bloqueada',
		toastDescription: (name) =>
			`Cerramos la sesión de ${name} y pausamos sus agentes. No podrá entrar hasta que actives su cuenta.`,
	},
	disabled: {
		title: (name) => `¿Desactivar la cuenta de ${name}?`,
		description:
			'Úsalo cuando la cuenta ya no se va a usar. Cerramos su sesión ahora mismo y no podrá entrar. Sus datos no se borran y puedes activarla más adelante.',
		toastTitle: 'Cuenta desactivada',
		toastDescription: (name) =>
			`Cerramos la sesión de ${name} y pausamos sus agentes. Ya no podrá entrar.`,
	},
	active: {
		title: (name) => `¿Activar la cuenta de ${name}?`,
		description:
			'Podrá volver a entrar con el código que le llega al correo. Sus agentes pausados siguen en pausa: los reanuda ella cuando entre.',
		toastTitle: 'Cuenta activada',
		toastDescription: (name) => `${name} ya puede entrar con su código.`,
	},
};

/**
 * Confirmación para activar, bloquear o desactivar la cuenta de otra persona.
 * Al bloquear o desactivar avisa que sus agentes se pausan (el backend lo
 * hace en el mismo paso) y que sus posiciones abiertas siguen protegidas.
 */
export function UserStatusDialog({
	change,
	onOpenChange,
}: UserStatusDialogProps) {
	const updateMutation = useUpdateUserStatusMutation();
	// Se recuerda el último cambio para que el texto no desaparezca durante la
	// animación de cierre.
	const [last, setLast] = useState<UserStatusChange | null>(change);
	if (change && change !== last) setLast(change);
	const current = change ?? last;

	const copy = current ? COPY[current.status] : null;
	const name = current ? userDisplayName(current.user) : '';
	const deactivating = !!current && current.status !== 'active';

	function confirm() {
		if (!change) return;
		const changeName = userDisplayName(change.user);
		updateMutation.mutate(
			{ id: change.user.id, status: change.status },
			{
				onSuccess: () => {
					toast.add({
						title: COPY[change.status].toastTitle,
						description: COPY[change.status].toastDescription(changeName),
						type: 'success',
					});
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos cambiar el estado',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<AlertDialog open={change !== null} onOpenChange={onOpenChange}>
			<AlertDialogContent>
				<AlertDialogHeader>
					<AlertDialogTitle>{copy?.title(name)}</AlertDialogTitle>
					<AlertDialogDescription>{copy?.description}</AlertDialogDescription>
				</AlertDialogHeader>
				{deactivating && (
					<Alert>
						<IconAlertTriangle />
						<AlertTitle>Pausamos sus agentes</AlertTitle>
						<AlertDescription>
							Sus agentes activos dejan de abrir operaciones nuevas. Las
							posiciones que ya tienen abiertas siguen protegidas con su stop
							loss y take profit. Si reactivas la cuenta, los agentes siguen en
							pausa hasta que la persona los reanude.
						</AlertDescription>
					</Alert>
				)}
				<AlertDialogFooter>
					<AlertDialogCancel>Cancelar</AlertDialogCancel>
					<AlertDialogAction
						variant={deactivating ? 'destructive' : 'default'}
						disabled={updateMutation.isPending}
						onClick={confirm}
					>
						{updateMutation.isPending && (
							<IconLoader2 className="animate-spin" />
						)}
						{current ? USER_STATUS_ACTION_LABELS[current.status] : ''}
					</AlertDialogAction>
				</AlertDialogFooter>
			</AlertDialogContent>
		</AlertDialog>
	);
}
