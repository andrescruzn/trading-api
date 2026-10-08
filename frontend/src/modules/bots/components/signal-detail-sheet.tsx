import { IconCircleCheck, IconCircleX } from '@tabler/icons-react';
import type { ReactNode } from 'react';
import type { Signal, SignalReasons } from '@/modules/bots/api/bots.api';
import { SignalActionBadge } from '@/modules/bots/components/bot-badges';
import { formatRiskReward, rejectionLabel } from '@/modules/bots/lib/bots-labels';
import {
	formatDateTime,
	formatNumber,
	formatPercent,
	formatPrice,
} from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import {
	Sheet,
	SheetContent,
	SheetDescription,
	SheetHeader,
	SheetTitle,
} from '@/modules/ui/components/sheet';
import { cn } from '@/modules/ui/lib/utils';

type SignalDetailSheetProps = {
	/** `null` = cerrado. */
	signal: Signal | null;
	onOpenChange: (open: boolean) => void;
};

function DetailItem({
	label,
	children,
	className,
}: {
	label: string;
	children: ReactNode;
	className?: string;
}) {
	return (
		<div className="flex flex-col gap-1">
			<dt className="text-xs text-muted-foreground">{label}</dt>
			<dd className={cn('font-medium tabular-nums', className)}>{children}</dd>
		</div>
	);
}

function CheckRow({ label, passed }: { label: string; passed: boolean | undefined }) {
	if (passed === undefined) return null;
	return (
		<li className="flex items-center gap-2">
			{passed ? (
				<IconCircleCheck className="size-4 text-chart-1" />
			) : (
				<IconCircleX className="size-4 text-destructive" />
			)}
			<span>{label}</span>
			<span className="sr-only">{passed ? 'cumple' : 'no cumple'}</span>
		</li>
	);
}

function formatRuleValue(value: unknown): string {
	if (typeof value === 'number') return formatNumber(value);
	if (value === null || value === undefined || value === '') return '—';
	return String(value);
}

/** Detalle de solo lectura de una señal: niveles, filtros y razonamiento del agente. */
export function SignalDetailSheet({ signal, onOpenChange }: SignalDetailSheetProps) {
	const reasons: SignalReasons = signal?.reasons ?? {};
	const rejection = rejectionLabel(reasons.rejection_reason);
	const rules = Array.isArray(reasons.rules_detail) ? reasons.rules_detail : [];

	return (
		<Sheet open={!!signal} onOpenChange={onOpenChange}>
			<SheetContent className="data-[side=right]:sm:max-w-lg">
				{signal && (
					<>
						<SheetHeader className="pr-14">
							<SheetTitle>Señal #{signal.id}</SheetTitle>
							<SheetDescription>{formatDateTime(signal.ts)}</SheetDescription>
						</SheetHeader>
						<div className="flex flex-col gap-6 overflow-y-auto px-4 pb-6">
							<div className="flex flex-wrap items-center gap-2">
								<SignalActionBadge action={signal.action} />
								<Badge variant={signal.approved ? 'secondary' : 'destructive'}>
									{signal.approved ? 'Aprobada' : 'Rechazada'}
								</Badge>
							</div>

							<dl className="grid grid-cols-2 gap-4">
								<DetailItem label="Entrada">{formatPrice(signal.entry_price)}</DetailItem>
								<DetailItem label="Stop loss" className="text-destructive">
									{formatPrice(signal.stop_loss)}
								</DetailItem>
								<DetailItem label="Take profit" className="text-chart-1">
									{formatPrice(signal.take_profit)}
								</DetailItem>
								<DetailItem label="Riesgo/beneficio">
									{formatRiskReward(signal.rr_ratio)}
								</DetailItem>
								<DetailItem label="Tamaño de posición">
									{formatNumber(signal.position_size)}
								</DetailItem>
								<DetailItem label="Confianza">
									{formatPercent(signal.confidence, 0)}
								</DetailItem>
							</dl>

							{rejection && (
								<section className="flex flex-col gap-1">
									<h3 className="text-sm font-medium">Motivo del rechazo</h3>
									<p className="text-sm text-destructive">{rejection}</p>
								</section>
							)}

							<section className="flex flex-col gap-2">
								<h3 className="text-sm font-medium">Filtros</h3>
								<ul className="flex flex-col gap-1.5 text-sm">
									<CheckRow label="Régimen de mercado" passed={reasons.regime_check_passed} />
									<CheckRow label="Reglas de la estrategia" passed={reasons.rules_check_passed} />
									<CheckRow
										label="Riesgo/beneficio mínimo de 2:1"
										passed={reasons.rr_check_passed}
									/>
								</ul>
							</section>

							{rules.length > 0 && (
								<section className="flex flex-col gap-2">
									<h3 className="text-sm font-medium">Reglas evaluadas</h3>
									<ul className="flex flex-col gap-1.5 text-sm">
										{rules.map((rule, index) => (
											<li key={`${rule.indicator}-${index}`} className="flex items-start gap-2">
												{rule.passed ? (
													<IconCircleCheck className="mt-0.5 size-4 shrink-0 text-chart-1" />
												) : (
													<IconCircleX className="mt-0.5 size-4 shrink-0 text-destructive" />
												)}
												<span className="font-mono text-xs leading-5">
													{rule.indicator} {rule.operator} {formatRuleValue(rule.threshold)}
													<span className="text-muted-foreground">
														{' '}
														(actual: {formatRuleValue(rule.actual_value)})
													</span>
												</span>
											</li>
										))}
									</ul>
								</section>
							)}

							{reasons.reasoning && (
								<section className="flex flex-col gap-1">
									<h3 className="text-sm font-medium">Razonamiento del agente de IA</h3>
									<p className="text-sm leading-relaxed whitespace-pre-line text-muted-foreground">
										{reasons.reasoning}
									</p>
								</section>
							)}

							<details className="text-sm">
								<summary className="cursor-pointer text-muted-foreground">
									Ver datos completos del análisis
								</summary>
								<pre className="mt-2 max-h-64 overflow-auto rounded-md bg-muted p-3 font-mono text-xs break-all whitespace-pre-wrap">
									{JSON.stringify(reasons, null, 2)}
								</pre>
							</details>
						</div>
					</>
				)}
			</SheetContent>
		</Sheet>
	);
}
