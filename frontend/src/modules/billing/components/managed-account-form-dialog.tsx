import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import { botOptions } from '@/modules/alerts/lib/alerts-labels';
import type {
	ManagedAccount,
	ManagedAccountUpdate,
	PeriodType,
} from '@/modules/billing/api/billing.api';
import {
	useCreateManagedAccountMutation,
	useUpdateManagedAccountMutation,
} from '@/modules/billing/hooks/use-billing-mutations';
import { useInvestorsQuery } from '@/modules/billing/hooks/use-billing-queries';
import {
	accountOptions,
	investorOptions,
	PERIOD_TYPE_OPTIONS,
} from '@/modules/billing/lib/billing-labels';
import { useBotsQuery } from '@/modules/bots/hooks/use-bots-queries';
import { useSymbolsQuery } from '@/modules/market/hooks/use-market-queries';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
import { Button } from '@/modules/ui/components/button';
import { Checkbox } from '@/modules/ui/components/checkbox';
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

// Valor del select de bot cuando la cuenta no tiene bot asignado.
const NO_BOT = 'none';

const managedAccountSchema = z.object({
	name: z
		.string()
		.trim()
		.min(2, 'Escribe al menos 2 caracteres')
		.max(120, 'Máximo 120 caracteres'),
	investor_id: requiredSelectField('Elige el inversor'),
	account_id: requiredSelectField('Elige la cuenta'),
	// Monto como texto: viaja tal cual a la API (DECIMAL) sin pasar por float.
	initial_capital: z
		.string()
		.trim()
		.min(1, 'Escribe el capital inicial')
		.refine(
			(value) => Number.isFinite(Number(value)) && Number(value) >= 0,
			'Debe ser un número mayor o igual a 0',
		),
	bot_id: z.string().nullable(),
	period_type: requiredSelectField('Elige la frecuencia de facturación'),
	is_active: z.boolean(),
});

type ManagedAccountFormInput = z.input<typeof managedAccountSchema>;
type ManagedAccountFormOutput = z.output<typeof managedAccountSchema>;

type ManagedAccountFormDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	/** `null` = crear; una cuenta = editar (inversor, cuenta y capital no se cambian). */
	managedAccount: ManagedAccount | null;
};

export function ManagedAccountFormDialog({
	open,
	onOpenChange,
	managedAccount,
}: ManagedAccountFormDialogProps) {
	const isEdit = !!managedAccount;
	const investorsQuery = useInvestorsQuery({ only_active: true });
	const accountsQuery = useAccountsQuery();
	const botsQuery = useBotsQuery();
	const symbolsQuery = useSymbolsQuery();
	const createMutation = useCreateManagedAccountMutation();
	const updateMutation = useUpdateManagedAccountMutation();
	const isPending = createMutation.isPending || updateMutation.isPending;

	const form = useForm<
		ManagedAccountFormInput,
		unknown,
		ManagedAccountFormOutput
	>({
		resolver: zodResolver(managedAccountSchema),
		defaultValues: {
			name: '',
			investor_id: null,
			account_id: null,
			initial_capital: '',
			bot_id: NO_BOT,
			period_type: 'monthly',
			is_active: true,
		},
	});
	const selectedAccountId = useWatch({
		control: form.control,
		name: 'account_id',
	});

	useEffect(() => {
		if (!open) return;
		form.reset({
			name: managedAccount?.name ?? '',
			investor_id: managedAccount ? String(managedAccount.investor_id) : null,
			account_id: managedAccount ? String(managedAccount.account_id) : null,
			initial_capital: managedAccount?.initial_capital ?? '',
			bot_id: managedAccount?.bot_id ? String(managedAccount.bot_id) : NO_BOT,
			period_type: managedAccount?.period_type ?? 'monthly',
			is_active: managedAccount?.is_active ?? true,
		});
	}, [open, managedAccount, form]);

	// Solo los bots que operan la cuenta elegida.
	const accountBots = (botsQuery.data ?? []).filter(
		(bot) => !selectedAccountId || String(bot.account_id) === selectedAccountId,
	);
	// El backend no permite quitar el bot de una cuenta existente: si ya tiene
	// uno, solo se ofrece cambiarlo.
	const canRemoveBot = !managedAccount?.bot_id;
	const botSelectOptions = [
		...(canRemoveBot ? [{ value: NO_BOT, label: 'Sin bot' }] : []),
		...botOptions(accountBots, symbolsQuery.data),
	];

	function handleSubmit(values: ManagedAccountFormOutput) {
		const botId =
			values.bot_id && values.bot_id !== NO_BOT ? Number(values.bot_id) : null;
		const periodType = values.period_type as PeriodType;
		const callbacks = {
			onSuccess: () => {
				toast.add({
					title: isEdit
						? 'Cuenta gestionada actualizada'
						: 'Cuenta gestionada creada',
					type: 'success',
				});
				onOpenChange(false);
			},
			onError: (error: unknown) =>
				toast.add({
					title: isEdit
						? 'No pudimos actualizar la cuenta gestionada'
						: 'No pudimos crear la cuenta gestionada',
					description: getErrorMessage(error),
					type: 'error',
				}),
		};

		if (managedAccount) {
			const input: ManagedAccountUpdate = {
				name: values.name,
				period_type: periodType,
				is_active: values.is_active,
			};
			if (botId) input.bot_id = botId;
			updateMutation.mutate({ id: managedAccount.id, input }, callbacks);
		} else {
			createMutation.mutate(
				{
					name: values.name,
					investor_id: Number(values.investor_id),
					account_id: Number(values.account_id),
					initial_capital: values.initial_capital,
					period_type: periodType,
					bot_id: botId,
				},
				callbacks,
			);
		}
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle>
						{isEdit ? 'Editar cuenta gestionada' : 'Nueva cuenta gestionada'}
					</DialogTitle>
					<DialogDescription>
						Cuenta de trading que se opera en nombre de un inversor y sobre la
						que se cobra la comisión de desempeño.
					</DialogDescription>
				</DialogHeader>
				<form
					id="managed-account-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="name"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="managed-account-name" required>
											Nombre
										</FieldLabel>
										<Input
											{...field}
											id="managed-account-name"
											placeholder="Portafolio BTC de Juan"
											maxLength={120}
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							{!isEdit && (
								<>
									<div className="grid gap-4 sm:grid-cols-2">
										<Controller
											name="investor_id"
											control={form.control}
											render={({ field, fieldState }) => (
												<Field data-invalid={fieldState.invalid}>
													<FieldLabel
														htmlFor="managed-account-investor"
														required
													>
														Inversor
													</FieldLabel>
													<OptionSelect
														id="managed-account-investor"
														value={field.value}
														onChange={field.onChange}
														options={investorOptions(investorsQuery.data)}
														aria-invalid={fieldState.invalid}
													/>
													{fieldState.invalid && (
														<FieldError errors={[fieldState.error]} />
													)}
												</Field>
											)}
										/>
										<Controller
											name="account_id"
											control={form.control}
											render={({ field, fieldState }) => (
												<Field data-invalid={fieldState.invalid}>
													<FieldLabel
														htmlFor="managed-account-account"
														required
													>
														Cuenta
													</FieldLabel>
													<OptionSelect
														id="managed-account-account"
														value={field.value}
														onChange={(value) => {
															field.onChange(value);
															// El bot elegido podría ser de otra cuenta.
															form.setValue('bot_id', NO_BOT);
														}}
														options={accountOptions(accountsQuery.data)}
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
										name="initial_capital"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="managed-account-capital" required>
													Capital inicial (USD)
												</FieldLabel>
												<Input
													{...field}
													id="managed-account-capital"
													type="number"
													inputMode="decimal"
													step="0.01"
													min={0}
													placeholder="10000"
													aria-invalid={fieldState.invalid}
												/>
												<FieldDescription>
													También es la marca de agua (HWM) inicial.
												</FieldDescription>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
								</>
							)}
							<div className="grid gap-4 sm:grid-cols-2">
								<Controller
									name="bot_id"
									control={form.control}
									render={({ field }) => (
										<Field>
											<FieldLabel htmlFor="managed-account-bot">Bot</FieldLabel>
											<OptionSelect
												id="managed-account-bot"
												value={field.value}
												onChange={field.onChange}
												options={botSelectOptions}
												placeholder="Sin bot"
											/>
											{!canRemoveBot && (
												<FieldDescription>
													Puedes cambiarlo, pero no quitarlo.
												</FieldDescription>
											)}
										</Field>
									)}
								/>
								<Controller
									name="period_type"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="managed-account-period" required>
												Facturación
											</FieldLabel>
											<OptionSelect
												id="managed-account-period"
												value={field.value}
												onChange={field.onChange}
												options={PERIOD_TYPE_OPTIONS}
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							</div>
							{isEdit && (
								<Controller
									name="is_active"
									control={form.control}
									render={({ field }) => (
										<Field orientation="horizontal">
											<Checkbox
												id="managed-account-active"
												checked={field.value}
												onCheckedChange={(checked) => field.onChange(checked)}
											/>
											<FieldLabel htmlFor="managed-account-active">
												Activa
											</FieldLabel>
										</Field>
									)}
								/>
							)}
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button
						type="submit"
						form="managed-account-form"
						disabled={isPending}
					>
						{isPending && <IconLoader2 className="animate-spin" />}
						{isEdit ? 'Guardar cambios' : 'Crear cuenta gestionada'}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
