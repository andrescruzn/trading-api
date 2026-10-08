import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useNavigate } from '@tanstack/react-router';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import { useChangePasswordMutation } from '@/modules/auth/hooks/use-auth-mutations';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import {
	Field,
	FieldDescription,
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

// Misma política que el backend (`ChangePasswordRequest` + `_validate_password_strength`).
const passwordSchema = z
	.object({
		currentPassword: z.string().min(1, 'Ingresa tu contraseña actual'),
		newPassword: z
			.string()
			.min(8, 'Mínimo 8 caracteres')
			.regex(/[A-Z]/, 'Incluye al menos una mayúscula')
			.regex(/[a-z]/, 'Incluye al menos una minúscula')
			.regex(/\d/, 'Incluye al menos un número'),
		confirmPassword: z.string().min(1, 'Confirma la nueva contraseña'),
	})
	.refine((values) => values.newPassword === values.confirmPassword, {
		path: ['confirmPassword'],
		message: 'Las contraseñas no coinciden',
	})
	.refine((values) => values.newPassword !== values.currentPassword, {
		path: ['newPassword'],
		message: 'La nueva contraseña debe ser distinta de la actual',
	});

type PasswordValues = z.infer<typeof passwordSchema>;

const FIELDS: {
	name: keyof PasswordValues;
	label: string;
	autoComplete: string;
	description?: string;
}[] = [
	{
		name: 'currentPassword',
		label: 'Contraseña actual',
		autoComplete: 'current-password',
	},
	{
		name: 'newPassword',
		label: 'Nueva contraseña',
		autoComplete: 'new-password',
		description:
			'Mínimo 8 caracteres, con al menos una mayúscula, una minúscula y un número.',
	},
	{
		name: 'confirmPassword',
		label: 'Confirmar nueva contraseña',
		autoComplete: 'new-password',
	},
];

export function ProfilePage() {
	usePageBreadcrumb([{ label: 'Cambiar contraseña' }]);
	const { user } = useAuth();
	const navigate = useNavigate();
	const changePasswordMutation = useChangePasswordMutation();

	const form = useForm<PasswordValues>({
		resolver: zodResolver(passwordSchema),
		defaultValues: {
			currentPassword: '',
			newPassword: '',
			confirmPassword: '',
		},
	});

	function handleSubmit(values: PasswordValues) {
		changePasswordMutation.mutate(
			{
				currentPassword: values.currentPassword,
				newPassword: values.newPassword,
			},
			{
				onSuccess: () => {
					toast.add({
						title: 'Cambiaste tu contraseña',
						description:
							'Por seguridad cerramos tu sesión. Ingresa con la nueva.',
						type: 'success',
					});
					navigate({ to: '/login' });
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos cambiar tu contraseña',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Cambiar contraseña"
				description={user ? `Sesión iniciada como ${user.email}` : undefined}
			/>
			<Card className="max-w-lg">
				<CardHeader>
					<CardTitle>Nueva contraseña</CardTitle>
					<CardDescription>
						Al guardar se cierra tu sesión y tendrás que volver a ingresar.
					</CardDescription>
				</CardHeader>
				<CardContent>
					<form onSubmit={form.handleSubmit(handleSubmit)} noValidate>
						<FieldGroup>
							{FIELDS.map((item) => (
								<Controller
									key={item.name}
									name={item.name}
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor={item.name} required>
												{item.label}
											</FieldLabel>
											<Input
												{...field}
												id={item.name}
												type="password"
												autoComplete={item.autoComplete}
												aria-invalid={fieldState.invalid}
											/>
											{item.description && !fieldState.invalid && (
												<FieldDescription>{item.description}</FieldDescription>
											)}
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							))}
							<Field orientation="horizontal" className="justify-end">
								<Button
									type="submit"
									disabled={changePasswordMutation.isPending}
								>
									{changePasswordMutation.isPending && (
										<IconLoader2 className="animate-spin" />
									)}
									Guardar contraseña
								</Button>
							</Field>
						</FieldGroup>
					</form>
				</CardContent>
			</Card>
		</div>
	);
}
