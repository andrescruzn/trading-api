import { Progress as ProgressPrimitive } from '@base-ui/react/progress';
import { cn } from '@/modules/ui/lib/utils';

function Progress({
	className,
	children,
	value,
	...props
}: ProgressPrimitive.Root.Props) {
	return (
		<ProgressPrimitive.Root
			data-slot="progress"
			value={value}
			className={cn('flex flex-wrap gap-3', className)}
			{...props}
		>
			{children}
			<ProgressTrack>
				<ProgressIndicator />
			</ProgressTrack>
		</ProgressPrimitive.Root>
	);
}

function ProgressTrack({ className, ...props }: ProgressPrimitive.Track.Props) {
	return (
		<ProgressPrimitive.Track
			data-slot="progress-track"
			className={cn(
				'relative flex h-2 w-full items-center overflow-x-hidden rounded-full bg-muted',
				className,
			)}
			{...props}
		/>
	);
}

/**
 * Con `value={null}` la barra queda indeterminada: el indicador no tiene ancho
 * y se anima de lado a lado.
 */
function ProgressIndicator({
	className,
	...props
}: ProgressPrimitive.Indicator.Props) {
	return (
		<ProgressPrimitive.Indicator
			data-slot="progress-indicator"
			className={cn(
				'h-full rounded-full bg-primary transition-all data-indeterminate:w-1/3 data-indeterminate:animate-pulse',
				className,
			)}
			{...props}
		/>
	);
}

function ProgressLabel({ className, ...props }: ProgressPrimitive.Label.Props) {
	return (
		<ProgressPrimitive.Label
			data-slot="progress-label"
			className={cn('text-sm font-medium', className)}
			{...props}
		/>
	);
}

function ProgressValue({ className, ...props }: ProgressPrimitive.Value.Props) {
	return (
		<ProgressPrimitive.Value
			data-slot="progress-value"
			className={cn(
				'ml-auto text-sm text-muted-foreground tabular-nums',
				className,
			)}
			{...props}
		/>
	);
}

export {
	Progress,
	ProgressIndicator,
	ProgressLabel,
	ProgressTrack,
	ProgressValue,
};
