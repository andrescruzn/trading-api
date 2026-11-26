import { IconLoader2 } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import { useUpdateProfileMutation } from '@/modules/auth/hooks/use-auth-mutations';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
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
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

type ProfileDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
};

/** La persona cambia su nombre visible; correo y rol son de solo lectura. */
export function ProfileDialog({ open, onOpenChange }: ProfileDialogProps) {
	const { user } = useAuth();
	const updateMutation = useUpdateProfileMutation();
	const [name, setName] = useState('');

	useEffect(() => {
		if (open) setName(user?.full_name ?? '');
	}, [open, user?.full_name]);

	function save(event: React.FormEvent) {
		event.preventDefault();
		updateMutation.mutate(name.trim() || null, {
			onSuccess: () => {
				toast.add({ title: 'Perfil actualizado', type: 'success' });
				onOpenChange(false);
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos guardar tu perfil',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Mi perfil</DialogTitle>
					<DialogDescription>
						Tu nombre aparece en el saludo del inicio y en las vistas de
						administración.
					</DialogDescription>
				</DialogHeader>
				<form id="profile-form" onSubmit={save} noValidate className="contents">
					<DialogBody>
						<FieldGroup>
							<Field>
								<FieldLabel htmlFor="profile-name">Nombre</FieldLabel>
								<Input
									id="profile-name"
									value={name}
									maxLength={255}
									autoComplete="name"
									placeholder="Ana Pérez"
									onChange={(event) => setName(event.target.value)}
								/>
							</Field>
							<Field>
								<FieldLabel htmlFor="profile-email">Correo</FieldLabel>
								<Input id="profile-email" value={user?.email ?? ''} disabled />
								<FieldDescription>
									Es con el que entras: no se puede cambiar desde aquí. Tu rol (
									{user?.role_label ?? '—'}) lo asigna un administrador.
								</FieldDescription>
							</Field>
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button
						type="submit"
						form="profile-form"
						disabled={updateMutation.isPending}
					>
						{updateMutation.isPending && (
							<IconLoader2 className="animate-spin" />
						)}
						Guardar
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
