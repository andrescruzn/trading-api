import { IconAlertTriangle, IconLoader2 } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import { useOwners } from '@/modules/auth/hooks/use-users-queries';
import type { FundPool } from '@/modules/fund/api/fund.api';
import { FeeBreakdown } from '@/modules/fund/components/fee-tables';
import { useSettleAgentMutation } from '@/modules/fund/hooks/use-fund-pools-mutations';
import { useSettlementPreviewQuery } from '@/modules/fund/hooks/use-fund-pools-queries';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import {
	formatDateTime,
	formatNumber,
	formatSignedPrice,
} from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
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
import { Field, FieldLabel } from '@/modules/ui/components/field';
import { Skeleton } from '@/modules/ui/components/skeleton';
import { Textarea } from '@/modules/ui/components/textarea';
import { toast } from '@/modules/ui/components/toast';

const ALL = 'all';

function Row({ label, value }: { label: string; value: string }) {
	return (
		<div className="flex items-center justify-between gap-4 text-sm">
			<span className="text-muted-foreground">{label}</span>
			<span className="font-medium tabular-nums">{value}</span>
		</div>
	);
}

type SettleAgentDialogProps = {
	pool: FundPool | null;
	onClose: () => void;
};

/**
 * Liquidar: muestra la cuenta completa antes de confirmar (resultado desde
 * la última liquidación, valor de la unidad y quién entra) y lo que la
 * impide, si algo.
 */
export function SettleAgentDialog({ pool, onClose }: SettleAgentDialogProps) {
	const previewQuery = useSettlementPreviewQuery(pool?.id ?? null, !!pool);
	const owners = useOwners(ALL);
	const mutation = useSettleAgentMutation();
	const [note, setNote] = useState('');

	useEffect(() => {
		if (pool) setNote('');
	}, [pool]);

	const preview = previewQuery.data;
	const blocked = !preview || preview.blockers.length > 0;

	function settle() {
		if (!pool) return;
		mutation.mutate(
			{ poolId: pool.id, note: note.trim() || null },
			{
				onSuccess: () => {
					toast.add({
						title: 'Liquidación hecha',
						description: 'Ya puedes reanudar el agente.',
						type: 'success',
					});
					onClose();
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos liquidar el agente',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={!!pool} onOpenChange={(open) => !open && onClose()}>
			<DialogContent className="sm:max-w-xl">
				<DialogHeader>
					<DialogTitle>Liquidar «{pool?.agent?.name ?? 'agente'}»</DialogTitle>
					<DialogDescription>
						Calcula el saldo exacto del agente con todo lo que operó desde la
						última liquidación, paga las salidas pedidas (con su comisión) y
						aplica las asignaciones en cola. Se hace con el agente pausado y sin
						posiciones abiertas.
					</DialogDescription>
				</DialogHeader>
				<DialogBody>
					{previewQuery.isLoading ? (
						<div className="flex flex-col gap-2">
							<Skeleton className="h-5 w-full" />
							<Skeleton className="h-5 w-full" />
							<Skeleton className="h-5 w-2/3" />
						</div>
					) : previewQuery.error || !preview ? (
						<ErrorAlert
							title="No pudimos calcular la liquidación"
							error={previewQuery.error}
						/>
					) : (
						<div className="flex flex-col gap-4">
							{preview.blocker_messages.length > 0 && (
								<Alert variant="destructive">
									<IconAlertTriangle />
									<AlertTitle>Aún no se puede liquidar</AlertTitle>
									<AlertDescription>
										<ul className="list-disc pl-4">
											{preview.blocker_messages.map((message) => (
												<li key={message}>{message}</li>
											))}
										</ul>
									</AlertDescription>
								</Alert>
							)}
							<div className="flex flex-col gap-1.5 rounded-lg border p-3">
								<Row
									label="Saldo en la liquidación anterior"
									value={`${formatNumber(preview.previous_equity, 2)} USDT`}
								/>
								<Row
									label={`Resultado de ${preview.fills_count} ejecuciones`}
									value={formatSignedPrice(preview.trading_result)}
								/>
								<Row
									label="Saldo del agente ahora"
									value={`${formatNumber(preview.equity_before, 2)} USDT`}
								/>
								<Row
									label="Valor de una unidad (NAV)"
									value={formatNumber(preview.nav, 6)}
								/>
							</div>
							{Object.keys(preview.unvalued_fees).length > 0 && (
								<Alert>
									<IconAlertTriangle />
									<AlertTitle>Comisiones en otra moneda</AlertTitle>
									<AlertDescription>
										{Object.entries(preview.unvalued_fees)
											.map(
												([asset, amount]) => `${formatNumber(amount)} ${asset}`,
											)
											.join(', ')}{' '}
										no se restan del resultado. Conviene que la billetera pague
										las comisiones en USDT.
									</AlertDescription>
								</Alert>
							)}
							<div className="flex flex-col gap-2">
								<span className="text-sm font-medium">
									Entran {formatNumber(preview.allocated_amount, 2)} USDT
								</span>
								{preview.allocations.length === 0 ? (
									<span className="text-sm text-muted-foreground">
										No hay asignaciones en cola.
									</span>
								) : (
									<ul className="flex flex-col gap-2">
										{preview.allocations.map((allocation) => (
											<li
												key={allocation.id}
												className="flex items-center justify-between gap-4 text-sm"
											>
												<OwnerCell
													userId={allocation.user_id}
													users={owners.byId}
												/>
												<span className="tabular-nums">
													{formatNumber(allocation.amount, 2)} USDT →{' '}
													{formatNumber(allocation.units, 4)} unidades
												</span>
											</li>
										))}
									</ul>
								)}
								{preview.canceled.length > 0 && (
									<span className="text-sm text-destructive">
										{preview.canceled.length === 1
											? '1 asignación se cancelará: la persona ya no tiene ese saldo.'
											: `${preview.canceled.length} asignaciones se cancelarán: esas personas ya no tienen ese saldo.`}
									</span>
								)}
							</div>
							<div className="flex flex-col gap-2">
								<span className="text-sm font-medium">
									Salen {formatNumber(preview.redeemed_amount, 2)} USDT ·
									comisión {formatNumber(preview.fees_total, 2)} USDT
								</span>
								{preview.redemptions.length === 0 ? (
									<span className="text-sm text-muted-foreground">
										No hay salidas que se puedan aplicar.
									</span>
								) : (
									<ul className="flex flex-col gap-3">
										{preview.redemptions.map((redemption) => (
											<li
												key={redemption.id}
												className="flex flex-col gap-1 rounded-md border p-2 text-sm"
											>
												<div className="flex items-center justify-between gap-4">
													<OwnerCell
														userId={redemption.user_id}
														users={owners.byId}
													/>
													<span className="tabular-nums">
														{formatNumber(redemption.value, 2)} USDT − comisión{' '}
														{formatNumber(redemption.fee, 2)} ={' '}
														<span className="font-medium">
															{formatNumber(redemption.net, 2)}
														</span>
													</span>
												</div>
												<FeeBreakdown breakdown={redemption.breakdown} />
												{redemption.pending_amount &&
													Number(redemption.pending_amount) > 0 && (
														<span className="text-xs text-muted-foreground">
															{formatNumber(redemption.pending_amount, 2)} USDT
															aún no cumplen la permanencia: siguen en el
															agente.
														</span>
													)}
											</li>
										))}
									</ul>
								)}
								{preview.waiting_redemptions.length > 0 && (
									<span className="text-sm text-muted-foreground">
										{preview.waiting_redemptions.length === 1
											? '1 salida espera: su dinero aún no cumple la permanencia mínima'
											: `${preview.waiting_redemptions.length} salidas esperan: su dinero aún no cumple la permanencia mínima`}
										{preview.hold_cutoff
											? ` (entró después del ${formatDateTime(preview.hold_cutoff)}).`
											: '.'}
									</span>
								)}
							</div>
							<Row
								label="Saldo del agente después"
								value={`${formatNumber(preview.equity_after, 2)} USDT`}
							/>
							<Field>
								<FieldLabel htmlFor="settle-note">Nota (opcional)</FieldLabel>
								<Textarea
									id="settle-note"
									rows={2}
									maxLength={500}
									value={note}
									onChange={(event) => setNote(event.target.value)}
									placeholder="Ej.: Cierre de octubre."
								/>
							</Field>
						</div>
					)}
				</DialogBody>
				<DialogFooter>
					<Button variant="outline" onClick={onClose}>
						Cancelar
					</Button>
					<Button onClick={settle} disabled={blocked || mutation.isPending}>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Liquidar
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
