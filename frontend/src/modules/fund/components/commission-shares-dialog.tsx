import { IconLoader2 } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import type { UserSummary } from '@/modules/auth/api/users.api';
import { userDisplayName } from '@/modules/auth/hooks/use-users-queries';
import { ROLE_LABELS, type RoleCode } from '@/modules/auth/lib/roles';
import type { CommissionShares } from '@/modules/fund/api/fund-payouts.api';
import { useSetCommissionSharesMutation } from '@/modules/fund/hooks/use-fund-payouts-mutations';
import { formatPercentValue } from '@/modules/shared/lib/format';
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
	FieldDescription,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { Textarea } from '@/modules/ui/components/textarea';
import { toast } from '@/modules/ui/components/toast';
import { cn } from '@/modules/ui/lib/utils';

type CommissionSharesDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	/** Super admin y socios activos: los que pueden recibir comisión. */
	owners: UserSummary[];
	current: CommissionShares | null;
};

function parsePct(value: string) {
	const number = Number(value.trim().replace(',', '.') || '0');
	return Number.isFinite(number) ? number : Number.NaN;
}

/**
 * Cómo se reparte la comisión entre propietarios y socios. Suma 100 %; un 0
 * deja a la persona fuera. Guardar crea una versión nueva: lo ya repartido no
 * cambia.
 */
export function CommissionSharesDialog({
	open,
	onOpenChange,
	owners,
	current,
}: CommissionSharesDialogProps) {
	const mutation = useSetCommissionSharesMutation();
	const [values, setValues] = useState<Record<number, string>>({});
	const [note, setNote] = useState('');

	useEffect(() => {
		if (!open) return;
		const initial: Record<number, string> = {};
		for (const owner of owners) initial[owner.id] = '';
		for (const share of current?.shares ?? [])
			initial[share.user_id] = share.pct;
		setValues(initial);
		setNote('');
	}, [open, owners, current]);

	const total = Object.values(values).reduce(
		(sum, value) => sum + parsePct(value),
		0,
	);
	// Centésimas: evita que 33,33 + 33,33 + 33,34 falle por coma flotante
	const balanced = Math.round(total * 100) === 10000;
	const invalid = Object.values(values).some((value) => {
		const pct = parsePct(value);
		return Number.isNaN(pct) || pct < 0 || pct > 100;
	});

	function submit() {
		const shares = Object.entries(values)
			.filter(([, value]) => parsePct(value) > 0)
			.map(([userId, value]) => ({
				user_id: Number(userId),
				pct: value.trim().replace(',', '.'),
			}));
		mutation.mutate(
			{ shares, note: note.trim() || null },
			{
				onSuccess: () => {
					toast.add({ title: 'Reparto guardado', type: 'success' });
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos guardar el reparto',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle>Reparto de la comisión</DialogTitle>
					<DialogDescription>
						Qué % de cada comisión cobrada recibe cada propietario o socio. Debe
						sumar 100 %. Rige desde la próxima liquidación.
					</DialogDescription>
				</DialogHeader>
				<DialogBody>
					<div className="flex flex-col gap-4">
						{owners.map((owner) => (
							<Field key={owner.id} orientation="horizontal">
								<FieldLabel
									htmlFor={`share-${owner.id}`}
									className="flex-1 flex-col items-start gap-0"
								>
									<span>{userDisplayName(owner)}</span>
									<span className="text-xs font-normal text-muted-foreground">
										{owner.role_code
											? ROLE_LABELS[owner.role_code as RoleCode]
											: ''}
									</span>
								</FieldLabel>
								<Input
									id={`share-${owner.id}`}
									inputMode="decimal"
									className="w-28 text-right"
									placeholder="0"
									value={values[owner.id] ?? ''}
									onChange={(event) =>
										setValues((previous) => ({
											...previous,
											[owner.id]: event.target.value,
										}))
									}
								/>
							</Field>
						))}
						<div
							className={cn(
								'flex justify-between text-sm font-medium tabular-nums',
								!balanced && 'text-destructive',
							)}
						>
							<span>Total</span>
							<span>{formatPercentValue(total)}</span>
						</div>
						<Field>
							<FieldLabel htmlFor="shares-note">Nota (opcional)</FieldLabel>
							<Textarea
								id="shares-note"
								rows={2}
								maxLength={500}
								value={note}
								onChange={(event) => setNote(event.target.value)}
							/>
							<FieldDescription>
								Si alguien deja de ser socio, ponle 0 y guarda una versión
								nueva.
							</FieldDescription>
						</Field>
					</div>
				</DialogBody>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button
						onClick={submit}
						disabled={!balanced || invalid || mutation.isPending}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Guardar reparto
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
