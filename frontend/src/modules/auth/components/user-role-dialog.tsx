import { IconAlertTriangle, IconLoader2 } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import type { UserSummary } from '@/modules/auth/api/users.api';
import { useUpdateUserRoleMutation } from '@/modules/auth/hooks/use-users-mutations';
import { userDisplayName } from '@/modules/auth/hooks/use-users-queries';
import {
	ASSIGNABLE_ROLE_OPTIONS,
	ROLE_LABELS,
	ROLES,
	type RoleCode,
} from '@/modules/auth/lib/roles';
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

type UserRoleDialogProps = {
	/** `null` = cerrado. */
	user: UserSummary | null;
	onOpenChange: (open: boolean) => void;
};

/** Qué cambia para la persona: lo que gana o pierde con el rol nuevo. */
function roleChangeWarning(from: RoleCode | null, to: RoleCode) {
	if (to === ROLES.PARTNER) {
		return 'Verá toda la Administración en solo lectura: agentes, cuentas, órdenes, alertas e inversores de todos. No podrá crear, editar, pausar ni aprobar nada.';
	}
	if (from === ROLES.PARTNER) {
		return 'Dejará de ver la Administración. Solo verá lo suyo como inversor.';
	}
	return null;
}

export function UserRoleDialog({ user, onOpenChange }: UserRoleDialogProps) {
	const updateMutation = useUpdateUserRoleMutation();
	const [roleCode, setRoleCode] = useState<RoleCode | null>(null);

	useEffect(() => {
		if (user) setRoleCode(user.role_code);
	}, [user]);

	const changed = !!user && !!roleCode && roleCode !== user.role_code;
	const warning =
		changed && user ? roleChangeWarning(user.role_code, roleCode) : null;

	function save() {
		if (!user || !roleCode || !changed) return;
		updateMutation.mutate(
			{ id: user.id, roleCode },
			{
				onSuccess: () => {
					toast.add({
						title: 'Rol actualizado',
						description: `${userDisplayName(user)} ahora es ${ROLE_LABELS[roleCode]}. Aplica desde su siguiente acción en la app.`,
						type: 'success',
					});
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos cambiar el rol',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={!!user} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Cambiar rol</DialogTitle>
					<DialogDescription>
						{user ? `${userDisplayName(user)} · ${user.email}` : ''}
					</DialogDescription>
				</DialogHeader>
				<DialogBody>
					<div className="flex flex-col gap-4">
						<Field>
							<FieldLabel htmlFor="user-role" required>
								Rol
							</FieldLabel>
							<OptionSelect
								id="user-role"
								value={roleCode}
								onChange={(value) => setRoleCode(value as RoleCode | null)}
								options={ASSIGNABLE_ROLE_OPTIONS}
							/>
							<FieldDescription>
								El rol decide qué ve en el menú y qué puede hacer.
							</FieldDescription>
						</Field>
						{warning && (
							<Alert>
								<IconAlertTriangle />
								<AlertTitle>Antes de guardar</AlertTitle>
								<AlertDescription>{warning}</AlertDescription>
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
						disabled={!changed || updateMutation.isPending}
					>
						{updateMutation.isPending && (
							<IconLoader2 className="animate-spin" />
						)}
						Guardar rol
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
