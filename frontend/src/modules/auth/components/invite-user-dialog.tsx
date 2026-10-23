import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { useInviteUserMutation } from '@/modules/auth/hooks/use-users-mutations';
import {
	ASSIGNABLE_ROLE_OPTIONS,
	type RoleCode,
} from '@/modules/auth/lib/roles';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
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
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

const inviteSchema = z.object({
	email: z.email('Escribe un correo válido, por ejemplo nombre@empresa.com'),
	full_name: z.string().max(255, 'Máximo 255 caracteres'),
	role_code: requiredSelectField('Elige el rol'),
});

type InviteInput = z.input<typeof inviteSchema>;
type InviteOutput = z.output<typeof inviteSchema>;

const EMPTY: InviteInput = { email: '', full_name: '', role_code: 'investor' };

type InviteUserDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
};

/** Registro solo por invitación: un super admin crea la cuenta y la persona entra con su código. */
export function InviteUserDialog({
	open,
	onOpenChange,
}: InviteUserDialogProps) {
	const inviteMutation = useInviteUserMutation();
	const form = useForm<InviteInput, unknown, InviteOutput>({
		resolver: zodResolver(inviteSchema),
		defaultValues: EMPTY,
	});

	useEffect(() => {
		if (open) form.reset(EMPTY);
	}, [open, form]);

	function handleSubmit(values: InviteOutput) {
		inviteMutation.mutate(
			{
				email: values.email.trim(),
				full_name: values.full_name.trim() || null,
				role_code: values.role_code as RoleCode,
			},
			{
				onSuccess: () => {
					toast.add({
						title: 'Usuario creado',
						description: `Le enviamos un correo a ${values.email.trim()} para que entre con su código.`,
						type: 'success',
					});
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos crear el usuario',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Invitar usuario</DialogTitle>
					<DialogDescription>
						La cuenta queda activa al instante. La persona recibe un correo y
						entra con su correo y el código que le enviamos; no hay contraseñas.
					</DialogDescription>
				</DialogHeader>
				<form
					id="invite-user-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="email"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="invite-email" required>
											Correo
										</FieldLabel>
										<Input
											{...field}
											id="invite-email"
											type="email"
											autoComplete="off"
											placeholder="nombre@empresa.com"
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="full_name"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="invite-name">Nombre</FieldLabel>
										<Input
											{...field}
											id="invite-name"
											autoComplete="off"
											placeholder="Ana Pérez"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Opcional. Así aparece en las vistas de administración.
										</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="role_code"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="invite-role" required>
											Rol
										</FieldLabel>
										<OptionSelect
											id="invite-role"
											value={field.value}
											onChange={field.onChange}
											options={ASSIGNABLE_ROLE_OPTIONS}
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button
						type="submit"
						form="invite-user-form"
						disabled={inviteMutation.isPending}
					>
						{inviteMutation.isPending && (
							<IconLoader2 className="animate-spin" />
						)}
						Crear e invitar
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
