import type { ReactNode } from 'react';
import {
	Card,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { Skeleton } from '@/modules/ui/components/skeleton';
import { cn } from '@/modules/ui/lib/utils';

type StatCardProps = {
	label: string;
	value: ReactNode;
	/** Línea secundaria bajo el valor (variación, badge, contexto). */
	hint?: ReactNode;
	icon?: ReactNode;
	isLoading?: boolean;
	className?: string;
};

/** Tarjeta de KPI: etiqueta, valor grande y una línea de contexto. */
export function StatCard({
	label,
	value,
	hint,
	icon,
	isLoading,
	className,
}: StatCardProps) {
	return (
		<Card className={cn('gap-2', className)}>
			<CardHeader>
				<CardDescription className="flex items-center justify-between gap-2">
					<span>{label}</span>
					{icon && <span className="text-muted-foreground">{icon}</span>}
				</CardDescription>
				<CardTitle className="text-2xl font-semibold tabular-nums">
					{isLoading ? <Skeleton className="h-8 w-32" /> : value}
				</CardTitle>
				{hint && !isLoading && (
					<div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
						{hint}
					</div>
				)}
			</CardHeader>
		</Card>
	);
}
