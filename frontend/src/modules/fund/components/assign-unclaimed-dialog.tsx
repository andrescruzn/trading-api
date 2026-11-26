import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { useOwners } from '@/modules/auth/hooks/use-users-queries';
import type { ExchangeDeposit } from '@/modules/fund/api/fund.api';
import { useAssignUnclaimedMutation } from '@/modules/fund/hooks/use-fund-mutations';
import { requiredText } from '@/modules/fund/lib/fund-forms';
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
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Textarea } from '@/modules/ui/components/textarea';
import { toast } from '@/modules/ui/components/toast';

const ALL = 'all';

const assignSchema = z.object({
	user_id: requiredSelectField('Elige a quién pertenece'),
	note: requiredText('Escribe cómo sabes que es de esa persona'),
});

type AssignInput = z.input<typeof assignSchema>;
type AssignOutput = z.output<typeof assignSchema>;

type AssignUnclaimedDialogProps = {
	deposit: ExchangeDeposit | null;
	onClose: () => void;
};

/** Un super admin asigna un depósito sin solicitud a su dueño y lo acredita. */
export function AssignUnclaimedDialog({
	deposit,
	onClose,
}: AssignUnclaimedDialogProps) {
	const owners = useOwners(ALL);
	const mutation = useAssignUnclaimedMutation();
	const options = owners.options.filter((option) => option.value !== ALL);
	const form = useForm<AssignInput, unknown, AssignOutput>({
		resolver: zodResolver(assignSchema),
		defaultValues: { user_id: null, note: '' },
	});

	useEffect(() => {
		if (deposit) form.reset({ user_id: null, note: '' });
	}, [deposit, form]);

	function handleSubmit(values: AssignOutput) {
		if (!deposit) return;
		mutation.mutate(
			{
				txid: deposit.txid,
				user_id: Number(values.user_id),
				note: values.note,
			},
			{
				onSuccess: () => {
					toast.add({ title: 'Depósito asignado', type: 'success' });
					onClose();
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos asignar el depósito',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={!!deposit} onOpenChange={(open) => !open && onClose()}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Asignar depósito</DialogTitle>
					<DialogDescription>
						{deposit
							? `${formatNumber(deposit.amount)} ${deposit.asset} que entraron sin solicitud. Se acreditan al saldo pendiente de asignar de la persona que elijas.`
							: ''}
					</DialogDescription>
				</DialogHeader>
				<form
					id="assign-unclaimed-form"
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
										<FieldLabel htmlFor="assign-user" required>
											Persona
										</FieldLabel>
										<OptionSelect
											id="assign-user"
											value={field.value}
											onChange={field.onChange}
											options={options}
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="note"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="assign-note" required>
											Nota
										</FieldLabel>
										<Textarea
											{...field}
											id="assign-note"
											rows={3}
											placeholder="Ej.: Lo confirmó por WhatsApp con captura del envío."
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
						form="assign-unclaimed-form"
						disabled={mutation.isPending}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Asignar y acreditar
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
