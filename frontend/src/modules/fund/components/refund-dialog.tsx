import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { useRefundPendingMutation } from '@/modules/fund/hooks/use-fund-mutations';
import {
	positiveAmountField,
	requiredText,
} from '@/modules/fund/lib/fund-forms';
import { formatNumber } from '@/modules/shared/lib/format';
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
import { Textarea } from '@/modules/ui/components/textarea';
import { toast } from '@/modules/ui/components/toast';

const refundSchema = z.object({
	amount: positiveAmountField,
	reason: requiredText('Escribe el motivo (mínimo 5 caracteres)', 500, 5),
});

type RefundInput = z.input<typeof refundSchema>;
type RefundOutput = z.output<typeof refundSchema>;

export type RefundTarget = {
	userId: number;
	name: string;
	/** Saldo pendiente de asignar (el máximo que se puede devolver). */
	pending: string;
};

type RefundDialogProps = {
	target: RefundTarget | null;
	onClose: () => void;
};

/**
 * Devolución excepcional: solo saldo que aún no pasó por un agente. El
 * dinero se envía por fuera; aquí queda el asiento que lo explica.
 */
export function RefundDialog({ target, onClose }: RefundDialogProps) {
	const mutation = useRefundPendingMutation();
	const form = useForm<RefundInput, unknown, RefundOutput>({
		resolver: zodResolver(refundSchema),
		defaultValues: { amount: '', reason: '' },
	});

	useEffect(() => {
		if (target) form.reset({ amount: target.pending, reason: '' });
	}, [target, form]);

	function handleSubmit(values: RefundOutput) {
		if (!target) return;
		mutation.mutate(
			{ userId: target.userId, amount: values.amount, reason: values.reason },
			{
				onSuccess: () => {
					toast.add({
						title: 'Devolución registrada',
						description: 'Recuerda enviar el dinero desde el exchange.',
						type: 'success',
					});
					onClose();
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos registrar la devolución',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={!!target} onOpenChange={(open) => !open && onClose()}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Devolver saldo pendiente</DialogTitle>
					<DialogDescription>
						{target
							? `${target.name} tiene ${formatNumber(target.pending)} USDT pendientes de asignar. Usa esto solo en casos excepcionales: lo normal es que el dinero pase por un agente.`
							: ''}
					</DialogDescription>
				</DialogHeader>
				<form
					id="refund-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="amount"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="refund-amount" required>
											Monto (USDT)
										</FieldLabel>
										<Input
											{...field}
											id="refund-amount"
											inputMode="decimal"
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="reason"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="refund-reason" required>
											Motivo
										</FieldLabel>
										<Textarea
											{...field}
											id="refund-reason"
											rows={3}
											placeholder="Ej.: Depositó por error; se le devuelve a la misma dirección."
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
						form="refund-form"
						variant="destructive"
						disabled={mutation.isPending}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Registrar devolución
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
