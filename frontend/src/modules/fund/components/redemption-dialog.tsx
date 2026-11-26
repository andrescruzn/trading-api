import { IconLoader2 } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import type { Participation } from '@/modules/fund/api/fund.api';
import { useRequestRedemptionMutation } from '@/modules/fund/hooks/use-fund-payouts-mutations';
import { formatNumber } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
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
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

type RedemptionDialogProps = {
	participation: Participation | null;
	minHoldDays: number;
	onClose: () => void;
};

/**
 * La persona pide sacar dinero de un agente. Se aplica en su próxima
 * liquidación, al valor de unidad de ese momento, y solo sale lo que cumple
 * la permanencia mínima.
 */
export function RedemptionDialog({
	participation,
	minHoldDays,
	onClose,
}: RedemptionDialogProps) {
	const mutation = useRequestRedemptionMutation();
	const [all, setAll] = useState(true);
	const [amount, setAmount] = useState('');
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		if (participation) {
			setAll(true);
			setAmount('');
			setError(null);
		}
	}, [participation]);

	function submit() {
		if (!participation) return;
		const value = amount.trim().replace(',', '.');
		if (!all && !(Number.isFinite(Number(value)) && Number(value) > 0)) {
			setError('Escribe un monto mayor que 0');
			return;
		}
		mutation.mutate(
			{ pool_id: participation.pool_id, amount: all ? null : value },
			{
				onSuccess: () => {
					toast.add({
						title: 'Salida en cola',
						description: 'Se aplica en la próxima liquidación del agente.',
						type: 'success',
					});
					onClose();
				},
				onError: (err) =>
					toast.add({
						title: 'No pudimos pedir la salida',
						description: getErrorMessage(err),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={!!participation} onOpenChange={(open) => !open && onClose()}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>
						Sacar dinero de «{participation?.agent?.name ?? 'agente'}»
					</DialogTitle>
					<DialogDescription>
						Hoy vale {formatNumber(participation?.value ?? 0, 2)} USDT (a su
						última liquidación). Sale en la próxima liquidación, al valor de ese
						momento, y pasa a tu saldo disponible para retirarlo.
					</DialogDescription>
				</DialogHeader>
				<DialogBody>
					<div className="flex flex-col gap-4">
						<Field orientation="horizontal">
							<Checkbox
								id="redemption-all"
								checked={all}
								onCheckedChange={(checked) => setAll(checked === true)}
							/>
							<FieldLabel htmlFor="redemption-all">Sacar todo</FieldLabel>
						</Field>
						{!all && (
							<Field data-invalid={!!error}>
								<FieldLabel htmlFor="redemption-amount" required>
									Monto (USDT)
								</FieldLabel>
								<Input
									id="redemption-amount"
									inputMode="decimal"
									value={amount}
									onChange={(event) => {
										setAmount(event.target.value);
										setError(null);
									}}
									aria-invalid={!!error}
								/>
								{error && <FieldError errors={[{ message: error }]} />}
							</Field>
						)}
						<FieldDescription>
							Solo sale el dinero que lleva al menos {minHoldDays} días en el
							agente; lo más reciente sale en una liquidación posterior. Sobre
							la ganancia que salga se cobra la comisión de la tabla vigente.
						</FieldDescription>
					</div>
				</DialogBody>
				<DialogFooter>
					<Button variant="outline" onClick={onClose}>
						Cancelar
					</Button>
					<Button onClick={submit} disabled={mutation.isPending}>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Pedir salida
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
