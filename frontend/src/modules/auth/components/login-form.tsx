import { zodResolver } from '@hookform/resolvers/zod';
import { IconArrowLeft, IconLoader2 } from '@tabler/icons-react';
import { useNavigate } from '@tanstack/react-router';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { OtpRequestResult } from '@/modules/auth/api/auth.api';
import {
	useRequestOtpMutation,
	useVerifyOtpMutation,
} from '@/modules/auth/hooks/use-auth-mutations';
import { useCountdown } from '@/modules/shared/hooks/use-countdown';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Alert, AlertDescription } from '@/modules/ui/components/alert';
import { Button } from '@/modules/ui/components/button';
import {
	Field,
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import {
	InputOTP,
	InputOTPGroup,
	InputOTPSlot,
} from '@/modules/ui/components/input-otp';
import { toast } from '@/modules/ui/components/toast';
import { cn } from '@/modules/ui/lib/utils';

const emailSchema = z.object({
	email: z.email('Ingresa un correo válido'),
});

const codeSchema = z.object({
	code: z.string().length(6, 'El código debe tener 6 dígitos'),
});

// Errores del servidor van por toast, no inline — los campos solo muestran
// errores de validación del cliente (react-hook-form/zod).
function showServerErrorToast(error: unknown, title: string) {
	toast.add({ title, description: getErrorMessage(error), type: 'error' });
}

function formatCountdown(totalSeconds: number) {
	const minutes = Math.floor(totalSeconds / 60);
	const seconds = totalSeconds % 60;
	return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// El login es solo por código: no hay contraseñas en el sistema.
function OtpLoginForm() {
	const navigate = useNavigate();
	const [otpRequest, setOtpRequest] = useState<OtpRequestResult | null>(null);

	const requestOtpMutation = useRequestOtpMutation();
	const verifyOtpMutation = useVerifyOtpMutation();
	const expiresIn = useCountdown(otpRequest?.otp_expires_at ?? null);

	const emailForm = useForm({
		resolver: zodResolver(emailSchema),
		defaultValues: { email: '' },
	});

	const codeForm = useForm({
		resolver: zodResolver(codeSchema),
		defaultValues: { code: '' },
	});

	function handleRequestOtp(email: string) {
		requestOtpMutation.mutate(email, {
			onSuccess: (result) => {
				setOtpRequest(result);
				codeForm.reset();
			},
			onError: (error) =>
				showServerErrorToast(error, 'No pudimos enviarte el código'),
		});
	}

	function handleVerifyOtp(values: z.infer<typeof codeSchema>) {
		if (!otpRequest) return;
		verifyOtpMutation.mutate(
			{ email: otpRequest.email, code: values.code },
			{
				onSuccess: () => navigate({ to: '/dashboard' }),
				onError: (error) => showServerErrorToast(error, 'No pudiste ingresar'),
			},
		);
	}

	const isPending = verifyOtpMutation.isPending || requestOtpMutation.isPending;

	if (!otpRequest) {
		return (
			<form
				className={cn(
					'transition-opacity',
					requestOtpMutation.isPending && 'pointer-events-none opacity-70',
				)}
				onSubmit={emailForm.handleSubmit((values) =>
					handleRequestOtp(values.email),
				)}
				noValidate
			>
				<FieldGroup>
					<Controller
						name="email"
						control={emailForm.control}
						render={({ field, fieldState }) => (
							<Field data-invalid={fieldState.invalid}>
								<FieldLabel htmlFor="otp-email" required>
									Correo
								</FieldLabel>
								<Input
									{...field}
									id="otp-email"
									type="email"
									placeholder="nombre@correo.com"
									aria-invalid={fieldState.invalid}
									autoComplete="email"
								/>
								{fieldState.invalid && (
									<FieldError errors={[fieldState.error]} />
								)}
							</Field>
						)}
					/>
					<Field>
						<Button type="submit" disabled={requestOtpMutation.isPending}>
							{requestOtpMutation.isPending ? (
								<IconLoader2 className="animate-spin" />
							) : (
								'Enviarme un código'
							)}
						</Button>
					</Field>
				</FieldGroup>
			</form>
		);
	}

	return (
		<form
			className={cn(
				'transition-opacity',
				isPending && 'pointer-events-none opacity-70',
			)}
			onSubmit={codeForm.handleSubmit(handleVerifyOtp)}
			noValidate
		>
			<FieldGroup>
				<Button
					type="button"
					variant="ghost"
					size="sm"
					className="-ml-2.5 self-start"
					onClick={() => {
						setOtpRequest(null);
						codeForm.reset();
						verifyOtpMutation.reset();
						requestOtpMutation.reset();
					}}
				>
					<IconArrowLeft />
					Cambiar correo
				</Button>
				{/* Anti-enumeración: la API responde igual exista o no la cuenta. */}
				<p className="text-sm text-muted-foreground">
					Si{' '}
					<span className="font-medium text-foreground">
						{otpRequest.email}
					</span>{' '}
					tiene una cuenta, te enviamos un código de 6 dígitos. Revisa tu
					bandeja de entrada y la carpeta de spam.
				</p>
				{otpRequest.otp_code && (
					<Alert>
						<AlertDescription>
							Modo desarrollo: tu código es{' '}
							<span className="font-mono font-semibold">
								{otpRequest.otp_code}
							</span>
						</AlertDescription>
					</Alert>
				)}
				<Controller
					name="code"
					control={codeForm.control}
					render={({ field, fieldState }) => (
						<Field data-invalid={fieldState.invalid}>
							<FieldLabel htmlFor="otp-code" required>
								Código
							</FieldLabel>
							<InputOTP
								{...field}
								onChange={(value: string) => {
									field.onChange(value);
									verifyOtpMutation.reset();
								}}
								onComplete={() => codeForm.handleSubmit(handleVerifyOtp)()}
								id="otp-code"
								maxLength={6}
								aria-invalid={fieldState.invalid}
								autoFocus
							>
								<InputOTPGroup>
									{Array.from({ length: 6 }, (_, index) => (
										<InputOTPSlot key={index} index={index} />
									))}
								</InputOTPGroup>
							</InputOTP>
							{fieldState.invalid && <FieldError errors={[fieldState.error]} />}
						</Field>
					)}
				/>
				<Field>
					<Button type="submit" disabled={verifyOtpMutation.isPending}>
						{verifyOtpMutation.isPending ? (
							<IconLoader2 className="animate-spin" />
						) : (
							'Ingresar'
						)}
					</Button>
				</Field>
				<div className="flex flex-col items-center gap-1 text-center">
					<p className="text-sm text-muted-foreground">
						{expiresIn > 0
							? `El código vence en ${formatCountdown(expiresIn)}.`
							: 'El código venció. Pide uno nuevo.'}
					</p>
					<Button
						type="button"
						size="xs"
						variant="ghost"
						disabled={isPending}
						onClick={() => handleRequestOtp(otpRequest.email)}
					>
						{requestOtpMutation.isPending ? (
							<IconLoader2 className="animate-spin" />
						) : (
							'Enviar otro código'
						)}
					</Button>
				</div>
			</FieldGroup>
		</form>
	);
}

export function LoginForm({ className }: { className?: string }) {
	return (
		<div className={cn('flex flex-col gap-6', className)}>
			<div className="flex flex-col items-center gap-1 text-center">
				<h1 className="text-2xl font-bold">Iniciar sesión</h1>
				<p className="text-sm text-balance text-muted-foreground">
					Escribe tu correo y te enviamos un código para entrar.
				</p>
			</div>
			<OtpLoginForm />
		</div>
	);
}
