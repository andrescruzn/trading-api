import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { Account } from '@/modules/accounts/api/accounts.api';
import { useRecordBalanceMutation } from '@/modules/accounts/hooks/use-accounts-mutations';
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
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

// Los montos se validan como texto y viajan como string: así no se pierde
// precisión con decimales largos (el backend los guarda como DECIMAL).
const amountField = z
	.string()
	.trim()
	.min(1, 'Escribe el monto')
	.refine(
		(value) => Number.isFinite(Number(value)) && Number(value) >= 0,
		'Debe ser un número mayor o igual a 0',
	);

const balanceSchema = z.object({
	asset: z
		.string()
		.trim()
		.min(1, 'Escribe el activo')
		.max(32, 'Máximo 32 caracteres'),
	free: amountField,
	locked: amountField,
});

type BalanceValues = z.infer<typeof balanceSchema>;

type RecordBalanceDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	account: Account | null;
	/** Activo con el que arranca el formulario (p. ej. el del filtro). */
	defaultAsset?: string;
};

export function RecordBalanceDialog({
	open,
	onOpenChange,
	account,
	defaultAsset,
}: RecordBalanceDialogProps) {
	const recordMutation = useRecordBalanceMutation();

	const form = useForm<BalanceValues>({
		resolver: zodResolver(balanceSchema),
		defaultValues: { asset: '', free: '', locked: '0' },
	});

	useEffect(() => {
		if (!open) return;
		form.reset({
			asset: defaultAsset || account?.base_currency || '',
			free: '',
			locked: '0',
		});
	}, [open, account, defaultAsset, form]);

	function handleSubmit(values: BalanceValues) {
		if (!account) return;
		recordMutation.mutate(
			{
				accountId: account.id,
				input: {
					asset: values.asset.toUpperCase(),
					free: values.free,
					locked: values.locked,
				},
			},
			{
				onSuccess: () => {
					toast.add({ title: 'Balance registrado', type: 'success' });
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos registrar el balance',
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
					<DialogTitle>Registrar balance</DialogTitle>
					<DialogDescription>
						Saldo de un activo en este momento. El agente de IA usa el saldo
						libre en {account?.base_currency ?? 'la moneda base'} como capital.
					</DialogDescription>
				</DialogHeader>
				<form
					id="record-balance-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="asset"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="balance-asset" required>
											Activo
										</FieldLabel>
										<Input
											{...field}
											id="balance-asset"
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
							<div className="grid gap-4 sm:grid-cols-2">
								<Controller
									name="free"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="balance-free" required>
												Libre
											</FieldLabel>
											<Input
												{...field}
												id="balance-free"
												type="number"
												inputMode="decimal"
												min={0}
												step="any"
												placeholder="1000"
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
								<Controller
									name="locked"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="balance-locked" required>
												Bloqueado
											</FieldLabel>
											<Input
												{...field}
												id="balance-locked"
												type="number"
												inputMode="decimal"
												min={0}
												step="any"
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							</div>
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button
						type="submit"
						form="record-balance-form"
						disabled={recordMutation.isPending || !account}
					>
						{recordMutation.isPending && <IconLoader2 className="animate-spin" />}
						Registrar balance
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
