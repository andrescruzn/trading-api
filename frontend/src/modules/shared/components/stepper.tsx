import { IconCheck } from '@tabler/icons-react';
import { cn } from '@/modules/ui/lib/utils';

type StepperStep = {
	title: string;
	/** Resumen de lo elegido, visible cuando el paso ya está hecho. */
	summary?: string | null;
};

type StepperProps = {
	steps: StepperStep[];
	/** Índice del paso actual (0 = primero). */
	current: number;
	/** Permite volver a un paso ya hecho haciendo clic. */
	onStepClick?: (index: number) => void;
	className?: string;
};

/**
 * Pasos numerados de un asistente: hecho (check), actual (resaltado) y
 * pendiente. En móvil solo se ve el título del paso actual.
 */
function Stepper({ steps, current, onStepClick, className }: StepperProps) {
	return (
		<nav aria-label="Pasos" className={className}>
			<ol className="flex items-center gap-2">
				{steps.map((step, index) => {
					const isDone = index < current;
					const isCurrent = index === current;
					const canClick = isDone && !!onStepClick;
					return (
						<li
							key={step.title}
							className={cn(
								'flex min-w-0 items-center gap-2',
								index < steps.length - 1 && 'flex-1',
							)}
							aria-current={isCurrent ? 'step' : undefined}
						>
							<button
								type="button"
								disabled={!canClick}
								onClick={() => canClick && onStepClick(index)}
								className={cn(
									'flex min-w-0 items-center gap-2.5 rounded-lg text-left',
									canClick && 'cursor-pointer hover:opacity-80',
								)}
							>
								<span
									className={cn(
										'flex size-8 shrink-0 items-center justify-center rounded-full border text-sm font-semibold tabular-nums transition-colors',
										isDone &&
											'border-primary bg-primary text-primary-foreground',
										isCurrent &&
											'border-primary text-primary ring-4 ring-primary/15',
										!isDone && !isCurrent && 'text-muted-foreground',
									)}
								>
									{isDone ? <IconCheck className="size-4" /> : index + 1}
								</span>
								<span
									className={cn(
										'min-w-0 flex-col',
										isCurrent ? 'flex' : 'hidden md:flex',
									)}
								>
									<span
										className={cn(
											'truncate text-sm font-medium',
											!isCurrent && !isDone && 'text-muted-foreground',
										)}
									>
										{step.title}
									</span>
									{isDone && step.summary && (
										<span className="truncate text-xs text-muted-foreground">
											{step.summary}
										</span>
									)}
								</span>
							</button>
							{index < steps.length - 1 && (
								<span
									aria-hidden
									className={cn(
										'h-px min-w-4 flex-1 transition-colors',
										isDone ? 'bg-primary' : 'bg-border',
									)}
								/>
							)}
						</li>
					);
				})}
			</ol>
		</nav>
	);
}

export { Stepper };
