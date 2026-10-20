import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2, IconPlus } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type {
	CapitalMovementKind,
	ManagedAccount,
} from '@/modules/billing/api/billing.api';
import { CapitalMovementsTable } from '@/modules/billing/components/capital-movements-table';
import { useRecordCapitalMovementMutation } from '@/modules/billing/hooks/use-billing-mutations';
import { useCapitalMovementsQuery } from '@/modules/billing/hooks/use-billing-queries';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { StatCard } from '@/modules/shared/components/stat-card';
import { formatPrice } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
import { Button } from '@/modules/ui/components/button';
import {
	Field,
	FieldDescription,
	FieldError,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import {
	Sheet,
	SheetContent,
	SheetDescription,
	SheetHeader,
	SheetTitle,
} from '@/modules/ui/components/sheet';
import { toast } from '@/modules/ui/components/toast';

const KIND_OPTIONS = [
	{ value: 'deposit', label: 'Aporte (entra dinero)' },
	{ value: 'withdrawal', label: 'Retiro (sale dinero)' },
];

const movementSchema = z.object({
	kind: requiredSelectField('Elige si es un aporte o un retiro'),
	amount: z
		.string()
		.trim()
		.refine(
			(value) => Number(value.replace(',', '.')) > 0,
			'Escribe un monto mayor que 0',
		),
	notes: z.string().max(500, 'Máximo 500 caracteres'),
});

type MovementInput = z.input<typeof movementSchema>;
type MovementOutput = z.output<typeof movementSchema>;

const EMPTY: MovementInput = { kind: 'deposit', amount: '', notes: '' };

type CapitalMovementsSheetProps = {
	/** `null` = cerrado. */
	account: ManagedAccount | null;
	onClose: () => void;
};

/** Admin: aportes y retiros de una cuenta gestionada, con el formulario para registrarlos. */
export function CapitalMovementsSheet({
	account,
	onClose,
}: CapitalMovementsSheetProps) {
	const movementsQuery = useCapitalMovementsQuery(account?.id ?? null);
	const recordMutation = useRecordCapitalMovementMutation();
	const form = useForm<MovementInput, unknown, MovementOutput>({
		resolver: zodResolver(movementSchema),
		defaultValues: EMPTY,
	});

	useEffect(() => {
		if (account) form.reset(EMPTY);
	}, [account, form]);

	function handleSubmit(values: MovementOutput) {
		if (!account) return;
		recordMutation.mutate(
			{
				id: account.id,
				input: {
					kind: values.kind as CapitalMovementKind,
					amount: values.amount.replace(',', '.'),
					notes: values.notes.trim() || null,
				},
			},
			{
				onSuccess: () => {
					toast.add({
						title:
							values.kind === 'deposit'
								? 'Aporte registrado'
								: 'Retiro registrado',
						description: 'La marca de agua se ajustó en el mismo monto.',
						type: 'success',
					});
					form.reset(EMPTY);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos registrar el movimiento',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	const summary = movementsQuery.data;

	return (
		<Sheet open={account !== null} onOpenChange={(open) => !open && onClose()}>
			<SheetContent className="data-[side=right]:w-full data-[side=right]:sm:max-w-2xl">
				<SheetHeader className="pr-14">
					<SheetTitle>Aportes y retiros · {account?.name}</SheetTitle>
					<SheetDescription>
						Un aporte sube la marca de agua y la apertura del período abierto en
						el mismo monto; un retiro las baja. Así la comisión nunca se cobra
						sobre dinero depositado.
					</SheetDescription>
				</SheetHeader>
				<div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 pb-4">
					<div className="grid gap-3 sm:grid-cols-3">
						<StatCard
							label="Aportes"
							value={formatPrice(summary?.deposits ?? null)}
							isLoading={movementsQuery.isLoading}
						/>
						<StatCard
							label="Retiros"
							value={formatPrice(summary?.withdrawals ?? null)}
							isLoading={movementsQuery.isLoading}
						/>
						<StatCard
							label="Neto aportado"
							value={formatPrice(summary?.net ?? null)}
							hint={`Marca de agua actual: ${formatPrice(account?.high_water_mark ?? null)}`}
							isLoading={movementsQuery.isLoading}
						/>
					</div>
					<form
						onSubmit={form.handleSubmit(handleSubmit)}
						noValidate
						className="grid gap-3 rounded-lg border p-3 sm:grid-cols-2"
					>
						<Controller
							name="kind"
							control={form.control}
							render={({ field, fieldState }) => (
								<Field data-invalid={fieldState.invalid}>
									<FieldLabel htmlFor="movement-kind" required>
										Tipo
									</FieldLabel>
									<OptionSelect
										id="movement-kind"
										value={field.value}
										onChange={field.onChange}
										options={KIND_OPTIONS}
									/>
									{fieldState.invalid && (
										<FieldError errors={[fieldState.error]} />
									)}
								</Field>
							)}
						/>
						<Controller
							name="amount"
							control={form.control}
							render={({ field, fieldState }) => (
								<Field data-invalid={fieldState.invalid}>
									<FieldLabel htmlFor="movement-amount" required>
										Monto
									</FieldLabel>
									<Input
										{...field}
										id="movement-amount"
										inputMode="decimal"
										placeholder="1000"
										autoComplete="off"
										aria-invalid={fieldState.invalid}
									/>
									{fieldState.invalid && (
										<FieldError errors={[fieldState.error]} />
									)}
								</Field>
							)}
						/>
						<Controller
							name="notes"
							control={form.control}
							render={({ field, fieldState }) => (
								<Field
									data-invalid={fieldState.invalid}
									className="sm:col-span-2"
								>
									<FieldLabel htmlFor="movement-notes">Nota</FieldLabel>
									<Input
										{...field}
										id="movement-notes"
										placeholder="Referencia de la transferencia"
										autoComplete="off"
									/>
									<FieldDescription>
										Registra el movimiento cuando el dinero ya esté en la
										cuenta.
									</FieldDescription>
									{fieldState.invalid && (
										<FieldError errors={[fieldState.error]} />
									)}
								</Field>
							)}
						/>
						<div className="flex justify-end sm:col-span-2">
							<Button
								type="submit"
								size="sm"
								disabled={recordMutation.isPending}
							>
								{recordMutation.isPending ? (
									<IconLoader2 className="animate-spin" />
								) : (
									<IconPlus />
								)}
								Registrar movimiento
							</Button>
						</div>
					</form>
					<CapitalMovementsTable
						rows={summary?.movements}
						isLoading={movementsQuery.isLoading}
						error={movementsQuery.error}
						empty="Aún no hay aportes ni retiros en esta cuenta."
					/>
				</div>
			</SheetContent>
		</Sheet>
	);
}
