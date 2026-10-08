import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import type {
	BillingPeriod,
	ManagedAccount,
} from '@/modules/billing/api/billing.api';
import {
	useCloseBillingPeriodMutation,
	useOpenBillingPeriodMutation,
} from '@/modules/billing/hooks/use-billing-mutations';
import { pnlClassName } from '@/modules/billing/lib/billing-labels';
import {
	formatPercent,
	formatPrice,
	toNumber,
} from '@/modules/shared/lib/format';
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
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

// Montos como texto: viajan tal cual a la API (DECIMAL) sin pasar por float.
function equityField(requiredMessage: string) {
	return z
		.string()
		.trim()
		.min(1, requiredMessage)
		.refine(
			(value) => Number.isFinite(Number(value)) && Number(value) >= 0,
			'Debe ser un número mayor o igual a 0',
		);
}

// ======================================================================
// Abrir período
// ======================================================================

const openSchema = z.object({
	opening_equity: equityField('Escribe el equity de apertura'),
});

type OpenValues = z.infer<typeof openSchema>;

type OpenPeriodDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	managedAccount: ManagedAccount | null;
};

export function OpenPeriodDialog({
	open,
	onOpenChange,
	managedAccount,
}: OpenPeriodDialogProps) {
	const openMutation = useOpenBillingPeriodMutation();
	const form = useForm<OpenValues>({
		resolver: zodResolver(openSchema),
		defaultValues: { opening_equity: '' },
	});

	useEffect(() => {
		if (open) form.reset({ opening_equity: '' });
	}, [open, form]);

	function handleSubmit(values: OpenValues) {
		if (!managedAccount) return;
		openMutation.mutate(
			{ managed_account_id: managedAccount.id, opening_equity: values.opening_equity },
			{
				onSuccess: () => {
					toast.add({ title: 'Período abierto', type: 'success' });
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos abrir el período',
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
					<DialogTitle>Abrir período de facturación</DialogTitle>
					<DialogDescription>
						{managedAccount?.name}. Solo puede haber un período abierto por cuenta: cierra el
						anterior antes de abrir uno nuevo.
					</DialogDescription>
				</DialogHeader>
				<form
					id="open-period-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="opening_equity"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="opening-equity" required>
											Equity de apertura (USD)
										</FieldLabel>
										<Input
											{...field}
											id="opening-equity"
											type="number"
											inputMode="decimal"
											step="0.01"
											min={0}
											placeholder="10000"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Valor actual de la cuenta. La comisión de desempeño del inversor queda
											fijada para este período.
										</FieldDescription>
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
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button type="submit" form="open-period-form" disabled={openMutation.isPending}>
						{openMutation.isPending && <IconLoader2 className="animate-spin" />}
						Abrir período
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}

// ======================================================================
// Cerrar período
// ======================================================================

const closeSchema = z.object({
	closing_equity: equityField('Escribe el equity de cierre'),
});

type CloseValues = z.infer<typeof closeSchema>;

/**
 * Misma fórmula que el backend (`BillingPeriod.calculate_fee`), solo para
 * mostrar una estimación: el valor final lo calcula el servidor al cerrar.
 */
function estimateFee(period: BillingPeriod, highWaterMark: string, closing: number) {
	const opening = toNumber(period.opening_equity) ?? 0;
	const hwm = toNumber(highWaterMark) ?? 0;
	const feePct = toNumber(period.fee_pct) ?? 0;
	const gross = closing - Math.max(opening, hwm);
	const fee = gross > 0 ? gross * feePct : 0;
	return { gross, fee, net: gross - fee };
}

type ClosePeriodDialogProps = {
	/** `null` = cerrado. */
	period: BillingPeriod | null;
	managedAccount: ManagedAccount | null;
	onOpenChange: (open: boolean) => void;
	/** Recibe el período ya cerrado, con los montos calculados por el backend. */
	onClosed: (period: BillingPeriod) => void;
};

export function ClosePeriodDialog({
	period,
	managedAccount,
	onOpenChange,
	onClosed,
}: ClosePeriodDialogProps) {
	const closeMutation = useCloseBillingPeriodMutation();
	const form = useForm<CloseValues>({
		resolver: zodResolver(closeSchema),
		defaultValues: { closing_equity: '' },
	});
	const closingText = useWatch({ control: form.control, name: 'closing_equity' });

	useEffect(() => {
		if (period) form.reset({ closing_equity: '' });
	}, [period, form]);

	const closing = toNumber(closingText?.trim());
	const estimate =
		period && managedAccount && closing !== null && closing >= 0
			? estimateFee(period, managedAccount.high_water_mark, closing)
			: null;

	function handleSubmit(values: CloseValues) {
		if (!period) return;
		closeMutation.mutate(
			{ id: period.id, input: { closing_equity: values.closing_equity } },
			{
				onSuccess: (closed) => {
					toast.add({ title: 'Período cerrado', type: 'success' });
					onClosed(closed);
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos cerrar el período',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	const summary: [string, string][] = period
		? [
				['Equity de apertura', formatPrice(period.opening_equity)],
				['Comisión de desempeño', formatPercent(period.fee_pct)],
				['Marca de agua (HWM)', formatPrice(managedAccount?.high_water_mark)],
			]
		: [];

	return (
		<Dialog open={!!period} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>¿Cerrar el período #{period?.id}?</DialogTitle>
					<DialogDescription>
						Se calcula la comisión de desempeño sobre la ganancia por encima de la marca de
						agua. Un período cerrado no se puede reabrir.
					</DialogDescription>
				</DialogHeader>
				<form
					id="close-period-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<dl className="grid gap-x-4 gap-y-2 rounded-lg border p-3 sm:grid-cols-3">
								{summary.map(([label, value]) => (
									<div key={label} className="flex flex-col gap-0.5">
										<dt className="text-xs text-muted-foreground">{label}</dt>
										<dd className="font-mono tabular-nums">{value}</dd>
									</div>
								))}
							</dl>
							<Controller
								name="closing_equity"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="closing-equity" required>
											Equity de cierre (USD)
										</FieldLabel>
										<Input
											{...field}
											id="closing-equity"
											type="number"
											inputMode="decimal"
											step="0.01"
											min={0}
											placeholder="12000"
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							{estimate && (
								<div className="flex flex-col gap-1 text-sm">
									<p className="text-muted-foreground">Estimación antes de cerrar:</p>
									<p className="font-mono tabular-nums">
										PnL bruto{' '}
										<span className={pnlClassName(estimate.gross)}>
											{formatPrice(estimate.gross)}
										</span>{' '}
										· Comisión {formatPrice(estimate.fee)} · PnL neto{' '}
										<span className={pnlClassName(estimate.net)}>
											{formatPrice(estimate.net)}
										</span>
									</p>
								</div>
							)}
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button type="submit" form="close-period-form" disabled={closeMutation.isPending}>
						{closeMutation.isPending && <IconLoader2 className="animate-spin" />}
						Cerrar período
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
