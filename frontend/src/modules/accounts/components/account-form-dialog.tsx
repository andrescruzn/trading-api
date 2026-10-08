import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2, IconLock } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type {
	Account,
	AccountMode,
	AccountStatus,
} from '@/modules/accounts/api/accounts.api';
import {
	useCreateAccountMutation,
	useUpdateAccountMutation,
} from '@/modules/accounts/hooks/use-accounts-mutations';
import {
	ACCOUNT_MODE_OPTIONS,
	ACCOUNT_STATUS_OPTIONS,
} from '@/modules/accounts/lib/accounts-labels';
import { useExchangesQuery } from '@/modules/market/hooks/use-market-queries';
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
	FieldLegend,
	FieldSet,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

// Valor del select para "sin exchange": Base UI usa `null` para "sin selección".
const NO_EXCHANGE = 'none';

const accountSchema = z
	.object({
		name: z
			.string()
			.trim()
			.min(1, 'Escribe el nombre')
			.max(120, 'Máximo 120 caracteres'),
		mode: requiredSelectField('Elige el modo'),
		base_currency: z
			.string()
			.trim()
			.min(1, 'Escribe la moneda base')
			.max(16, 'Máximo 16 caracteres'),
		exchange_id: z.string().nullable(),
		status: requiredSelectField('Elige el estado'),
		api_key: z.string().trim(),
		api_secret: z.string().trim(),
		credentials_label: z.string().trim().max(255, 'Máximo 255 caracteres'),
	})
	// El backend solo guarda credenciales si llegan las dos juntas.
	.refine((values) => !values.api_key || !!values.api_secret, {
		message: 'Escribe el API secret',
		path: ['api_secret'],
	})
	.refine((values) => !values.api_secret || !!values.api_key, {
		message: 'Escribe la API key',
		path: ['api_key'],
	});

type AccountFormInput = z.input<typeof accountSchema>;
type AccountFormOutput = z.output<typeof accountSchema>;

type AccountFormDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	/** `null` = crear; una cuenta = editar (el modo no se cambia). */
	account: Account | null;
};

function valuesFor(account: Account | null): AccountFormInput {
	return {
		name: account?.name ?? '',
		mode: account?.mode ?? null,
		base_currency: account?.base_currency ?? 'USDT',
		exchange_id: account?.exchange_id
			? String(account.exchange_id)
			: NO_EXCHANGE,
		status: account?.status ?? 'active',
		// Los secretos nunca se precargan: vacío = conservar los actuales.
		api_key: '',
		api_secret: '',
		credentials_label: '',
	};
}

export function AccountFormDialog({
	open,
	onOpenChange,
	account,
}: AccountFormDialogProps) {
	const isEdit = !!account;
	const exchangesQuery = useExchangesQuery();
	const createMutation = useCreateAccountMutation();
	const updateMutation = useUpdateAccountMutation();
	const isPending = createMutation.isPending || updateMutation.isPending;

	const form = useForm<AccountFormInput, unknown, AccountFormOutput>({
		resolver: zodResolver(accountSchema),
		defaultValues: valuesFor(null),
	});

	// Al abrir arranca con los datos de la cuenta (o vacío al crear). Al cerrar
	// se borran las credenciales para que no queden en memoria del formulario.
	useEffect(() => {
		if (open) {
			form.reset(valuesFor(account));
		} else {
			form.setValue('api_key', '');
			form.setValue('api_secret', '');
		}
	}, [open, account, form]);

	function handleSubmit(values: AccountFormOutput) {
		const exchangeId =
			values.exchange_id && values.exchange_id !== NO_EXCHANGE
				? Number(values.exchange_id)
				: null;
		const credentials =
			values.api_key && values.api_secret
				? {
						api_key: values.api_key,
						api_secret: values.api_secret,
						credentials_label: values.credentials_label || undefined,
					}
				: {};
		const callbacks = {
			onSuccess: () => {
				toast.add({
					title: isEdit ? 'Cuenta actualizada' : 'Cuenta creada',
					type: 'success',
				});
				onOpenChange(false);
			},
			onError: (error: unknown) =>
				toast.add({
					title: isEdit
						? 'No pudimos actualizar la cuenta'
						: 'No pudimos crear la cuenta',
					description: getErrorMessage(error),
					type: 'error',
				}),
		};

		if (account) {
			updateMutation.mutate(
				{
					id: account.id,
					input: {
						name: values.name,
						status: values.status as AccountStatus,
						base_currency: values.base_currency.toUpperCase(),
						// El backend no permite quitar el exchange: `null` se omite.
						exchange_id: exchangeId ?? undefined,
						...credentials,
					},
				},
				callbacks,
			);
		} else {
			createMutation.mutate(
				{
					name: values.name,
					mode: values.mode as AccountMode,
					base_currency: values.base_currency.toUpperCase(),
					exchange_id: exchangeId,
					...credentials,
				},
				callbacks,
			);
		}
	}

	// Exchanges activos + el actual de la cuenta (aunque esté inactivo), para
	// que el select no se vacíe al editar.
	const exchangeOptions = [
		// Una cuenta con exchange no puede quedar sin él (el backend lo ignora).
		...(isEdit && account?.exchange_id
			? []
			: [{ value: NO_EXCHANGE, label: 'Sin exchange' }]),
		...(exchangesQuery.data ?? [])
			.filter(
				(exchange) =>
					exchange.is_active || exchange.id === account?.exchange_id,
			)
			.map((exchange) => ({
				value: String(exchange.id),
				label: exchange.name,
			})),
	];

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle>{isEdit ? 'Editar cuenta' : 'Nueva cuenta'}</DialogTitle>
					<DialogDescription>
						{account
							? account.name
							: 'Cuenta de exchange donde los bots registran sus órdenes, en modo paper o live.'}
					</DialogDescription>
				</DialogHeader>
				<form
					id="account-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					autoComplete="off"
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="name"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="account-name" required>
											Nombre
										</FieldLabel>
										<Input
											{...field}
											id="account-name"
											placeholder="Binance principal"
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<div className="grid gap-4 sm:grid-cols-2">
								{isEdit ? (
									<Controller
										name="status"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="account-status" required>
													Estado
												</FieldLabel>
												<OptionSelect
													id="account-status"
													value={field.value}
													onChange={field.onChange}
													options={ACCOUNT_STATUS_OPTIONS}
													aria-invalid={fieldState.invalid}
												/>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
								) : (
									<Controller
										name="mode"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="account-mode" required>
													Modo
												</FieldLabel>
												<OptionSelect
													id="account-mode"
													value={field.value}
													onChange={field.onChange}
													options={ACCOUNT_MODE_OPTIONS}
													placeholder="Elige el modo"
													aria-invalid={fieldState.invalid}
												/>
												<FieldDescription>
													No se puede cambiar después.
												</FieldDescription>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
								)}
								<Controller
									name="base_currency"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="account-currency" required>
												Moneda base
											</FieldLabel>
											<Input
												{...field}
												id="account-currency"
												placeholder="USDT"
												className="uppercase"
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							</div>
							<Controller
								name="exchange_id"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="account-exchange">Exchange</FieldLabel>
										<OptionSelect
											id="account-exchange"
											value={field.value}
											onChange={field.onChange}
											options={exchangeOptions}
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<FieldSet className="gap-4">
								<FieldLegend
									variant="label"
									className="mb-0 flex items-center gap-1.5"
								>
									<IconLock className="size-4 text-muted-foreground" />
									Credenciales del exchange
								</FieldLegend>
								<FieldDescription>
									{account?.has_credentials
										? 'La cuenta ya tiene credenciales guardadas. Déjalas vacías para conservarlas o escribe las nuevas para reemplazarlas.'
										: 'Opcionales. Se cifran antes de guardarse y no se vuelven a mostrar.'}
								</FieldDescription>
								<div className="grid gap-4 sm:grid-cols-2">
									<Controller
										name="api_key"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="account-api-key">
													API key
												</FieldLabel>
												<Input
													{...field}
													id="account-api-key"
													type="password"
													autoComplete="new-password"
													spellCheck={false}
													placeholder={
														account?.has_credentials ? 'Sin cambios' : undefined
													}
													aria-invalid={fieldState.invalid}
												/>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
									<Controller
										name="api_secret"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="account-api-secret">
													API secret
												</FieldLabel>
												<Input
													{...field}
													id="account-api-secret"
													type="password"
													autoComplete="new-password"
													spellCheck={false}
													placeholder={
														account?.has_credentials ? 'Sin cambios' : undefined
													}
													aria-invalid={fieldState.invalid}
												/>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
								</div>
								<Controller
									name="credentials_label"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="account-credentials-label">
												Etiqueta de las credenciales
											</FieldLabel>
											<Input
												{...field}
												id="account-credentials-label"
												placeholder="binance-principal"
												aria-invalid={fieldState.invalid}
											/>
											<FieldDescription>
												Para reconocerlas. Solo se guarda junto con una API key
												y un secret nuevos.
											</FieldDescription>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							</FieldSet>
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button type="submit" form="account-form" disabled={isPending}>
						{isPending && <IconLoader2 className="animate-spin" />}
						{isEdit ? 'Guardar cambios' : 'Crear cuenta'}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
