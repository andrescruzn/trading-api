import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import { useOwners } from '@/modules/auth/hooks/use-users-queries';
import type { FundPool, LedgerBucket } from '@/modules/fund/api/fund.api';
import { useQueueAllocationMutation } from '@/modules/fund/hooks/use-fund-pools-mutations';
import { useParticipantBalancesQuery } from '@/modules/fund/hooks/use-fund-queries';
import { positiveAmountField } from '@/modules/fund/lib/fund-forms';
import { ALLOCATION_SOURCE_OPTIONS } from '@/modules/fund/lib/fund-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { formatNumber } from '@/modules/shared/lib/format';
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

const ALL = 'all';

const allocationSchema = z.object({
	user_id: requiredSelectField('Elige de quién es el dinero'),
	source_bucket: requiredSelectField('Elige de qué saldo sale'),
	amount: positiveAmountField,
});

type AllocationInput = z.input<typeof allocationSchema>;
type AllocationOutput = z.output<typeof allocationSchema>;

type QueueAllocationDialogProps = {
	pool: FundPool | null;
	onClose: () => void;
};

/** Pone en cola dinero de una persona para un agente: entra al liquidar. */
export function QueueAllocationDialog({
	pool,
	onClose,
}: QueueAllocationDialogProps) {
	const owners = useOwners(ALL);
	const balancesQuery = useParticipantBalancesQuery();
	const mutation = useQueueAllocationMutation();
	const form = useForm<AllocationInput, unknown, AllocationOutput>({
		resolver: zodResolver(allocationSchema),
		defaultValues: { user_id: null, source_bucket: 'pending', amount: '' },
	});

	useEffect(() => {
		if (pool)
			form.reset({ user_id: null, source_bucket: 'pending', amount: '' });
	}, [pool, form]);

	const userId = useWatch({ control: form.control, name: 'user_id' });
	const source = useWatch({ control: form.control, name: 'source_bucket' });
	const balance = balancesQuery.data?.find((b) => b.user_id === Number(userId));
	const sourceBalance =
		balance && source ? balance[source as LedgerBucket] : undefined;

	// Solo personas con saldo en el fondo
	const withBalance = new Set(
		(balancesQuery.data ?? [])
			.filter((b) => Number(b.pending) > 0 || Number(b.available) > 0)
			.map((b) => b.user_id),
	);
	const options = owners.options.filter(
		(option) => option.value !== ALL && withBalance.has(Number(option.value)),
	);

	function handleSubmit(values: AllocationOutput) {
		if (!pool) return;
		mutation.mutate(
			{
				poolId: pool.id,
				userId: Number(values.user_id),
				amount: values.amount,
				sourceBucket: values.source_bucket as LedgerBucket,
			},
			{
				onSuccess: () => {
					toast.add({
						title: 'Asignación en cola',
						description: 'Entra al agente en la próxima liquidación.',
						type: 'success',
					});
					onClose();
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos poner la asignación en cola',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={!!pool} onOpenChange={(open) => !open && onClose()}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Asignar dinero al agente</DialogTitle>
					<DialogDescription>
						{pool?.agent
							? `«${pool.agent.name}». El dinero no se mueve ahora: entra al agente al liquidarlo, al valor de unidad de ese momento.`
							: ''}
					</DialogDescription>
				</DialogHeader>
				<form
					id="queue-allocation-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="user_id"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="allocation-user" required>
											Persona
										</FieldLabel>
										<OptionSelect
											id="allocation-user"
											value={field.value}
											onChange={field.onChange}
											options={options}
											placeholder={
												options.length === 0
													? 'Nadie tiene saldo en el fondo'
													: 'Elige a la persona'
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
								name="source_bucket"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="allocation-source" required>
											Sale de
										</FieldLabel>
										<OptionSelect
											id="allocation-source"
											value={field.value}
											onChange={field.onChange}
											options={ALLOCATION_SOURCE_OPTIONS}
											aria-invalid={fieldState.invalid}
										/>
										{sourceBalance !== undefined && (
											<FieldDescription>
												Tiene {formatNumber(sourceBalance, 2)} USDT en ese saldo
												(lo que ya tenga en cola se descuenta al guardar).
											</FieldDescription>
										)}
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
										<FieldLabel htmlFor="allocation-amount" required>
											Monto (USDT)
										</FieldLabel>
										<Input
											{...field}
											id="allocation-amount"
											inputMode="decimal"
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
					<Button variant="outline" onClick={onClose}>
						Cancelar
					</Button>
					<Button
						type="submit"
						form="queue-allocation-form"
						disabled={mutation.isPending}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Poner en cola
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
