import { useEquityEstimateQuery } from '@/modules/billing/hooks/use-billing-queries';
import { formatDateTime, formatPrice } from '@/modules/shared/lib/format';
import { Button } from '@/modules/ui/components/button';
import { Skeleton } from '@/modules/ui/components/skeleton';

type EquityEstimateHintProps = {
	managedAccountId: number | null;
	/** Solo se consulta con el diálogo abierto. */
	enabled: boolean;
	onUse: (equity: string) => void;
};

/** Equity sugerido desde los balances de la cuenta, con botón para usarlo. */
export function EquityEstimateHint({
	managedAccountId,
	enabled,
	onUse,
}: EquityEstimateHintProps) {
	const estimateQuery = useEquityEstimateQuery(managedAccountId, enabled);
	const estimate = estimateQuery.data;

	if (estimateQuery.isLoading) return <Skeleton className="h-12 w-full" />;
	if (estimateQuery.error || !estimate) return null;

	if (estimate.lines.length === 0) {
		return (
			<p className="text-sm text-muted-foreground">
				No hay balances registrados en esta cuenta para sugerir un valor.
			</p>
		);
	}

	return (
		<div className="flex flex-col gap-2 rounded-lg border bg-muted/40 p-3 text-sm">
			<div className="flex flex-wrap items-center justify-between gap-2">
				<p>
					Sugerido desde los balances:{' '}
					<span className="font-mono font-medium tabular-nums">
						{formatPrice(estimate.equity)}
					</span>{' '}
					<span className="text-muted-foreground">
						{estimate.currency}
						{estimate.as_of ? ` · al ${formatDateTime(estimate.as_of)}` : ''}
					</span>
				</p>
				<Button
					type="button"
					size="xs"
					variant="outline"
					onClick={() => onUse(String(Number(estimate.equity).toFixed(2)))}
				>
					Usar este valor
				</Button>
			</div>
			{estimate.missing.length > 0 && (
				<p className="text-muted-foreground">
					Sin precio, no suman: {estimate.missing.join(', ')}. Revisa su valor
					antes de usar el sugerido.
				</p>
			)}
		</div>
	);
}
