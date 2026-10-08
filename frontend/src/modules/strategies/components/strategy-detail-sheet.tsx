import type { ReactNode } from 'react';
import { formatDate, formatPercent } from '@/modules/shared/lib/format';
import type {
	Strategy,
	StrategyParameters,
} from '@/modules/strategies/api/strategies.api';
import { StrategyRegimeBadge } from '@/modules/strategies/components/strategy-regime-badge';
import {
	describeRule,
	strategyTypeLabel,
} from '@/modules/strategies/lib/strategies-labels';
import {
	Sheet,
	SheetContent,
	SheetDescription,
	SheetHeader,
	SheetTitle,
} from '@/modules/ui/components/sheet';

type StrategyDetailSheetProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	/** Se conserva al cerrar para que el contenido no desaparezca durante la animación. */
	strategy: Strategy | null;
};

function DetailItem({
	label,
	children,
}: {
	label: string;
	children: ReactNode;
}) {
	return (
		<div className="flex flex-col gap-1">
			<dt className="text-xs text-muted-foreground">{label}</dt>
			<dd className="font-medium">{children}</dd>
		</div>
	);
}

function SectionTitle({ children }: { children: ReactNode }) {
	return (
		<h3 className="text-xs font-medium text-muted-foreground">{children}</h3>
	);
}

export function StrategyDetailSheet({
	open,
	onOpenChange,
	strategy,
}: StrategyDetailSheetProps) {
	const parameters: StrategyParameters = strategy?.parameters ?? {};
	const rules = Array.isArray(parameters.rules) ? parameters.rules : [];

	return (
		<Sheet open={open} onOpenChange={onOpenChange}>
			<SheetContent className="w-full data-[side=right]:sm:max-w-lg">
				<SheetHeader className="pr-14">
					<SheetTitle>
						{strategy
							? `${strategy.name} · v${strategy.version}`
							: 'Estrategia'}
					</SheetTitle>
					<SheetDescription>
						Reglas que debe cumplir una operación para que el sistema la
						proponga.
					</SheetDescription>
				</SheetHeader>
				{strategy && (
					<div className="flex flex-1 flex-col gap-6 overflow-y-auto px-4 pb-6">
						<dl className="grid grid-cols-2 gap-4">
							<DetailItem label="Tipo">
								{strategyTypeLabel(parameters.strategy_type)}
							</DetailItem>
							<DetailItem label="Régimen requerido">
								<StrategyRegimeBadge regime={parameters.regime_required} />
							</DetailItem>
							<DetailItem label="Timeframe">
								<span className="font-mono">
									{parameters.timeframe_code || '—'}
								</span>
							</DetailItem>
							<DetailItem label="Versión">
								<span className="font-mono">{strategy.version}</span>
							</DetailItem>
							<DetailItem label="Riesgo por operación">
								{formatPercent(parameters.risk_pct)}
							</DetailItem>
							<DetailItem label="Creada">
								{formatDate(strategy.created_at)}
							</DetailItem>
						</dl>

						<section className="flex flex-col gap-2">
							<SectionTitle>Descripción</SectionTitle>
							<p
								className={
									strategy.description ? undefined : 'text-muted-foreground'
								}
							>
								{strategy.description || 'Sin descripción.'}
							</p>
						</section>

						<section className="flex flex-col gap-2">
							<SectionTitle>Reglas</SectionTitle>
							{rules.length === 0 ? (
								<p className="text-muted-foreground">Sin reglas definidas.</p>
							) : (
								<ul className="flex flex-col gap-1.5">
									{rules.map((rule, index) => {
										// Las reglas no tienen ID y pueden repetirse: el índice es su identidad.
										const key = `${index}-${describeRule(rule)}`;
										return (
											<li
												key={key}
												className="rounded-md bg-muted px-3 py-2 font-mono text-xs"
											>
												{describeRule(rule)}
											</li>
										);
									})}
								</ul>
							)}
						</section>

						<section className="flex flex-col gap-2">
							<SectionTitle>Parámetros (JSON completo)</SectionTitle>
							<pre className="max-h-72 overflow-auto rounded-md bg-muted p-3 font-mono text-xs break-all whitespace-pre-wrap text-muted-foreground">
								{JSON.stringify(parameters, null, 2)}
							</pre>
						</section>
					</div>
				)}
			</SheetContent>
		</Sheet>
	);
}
