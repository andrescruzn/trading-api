import { IconCircleCheckFilled } from '@tabler/icons-react';
import type { ReactNode } from 'react';
import { cn } from '@/modules/ui/lib/utils';

type ChoiceCardProps = {
	selected: boolean;
	onSelect: () => void;
	title: ReactNode;
	description?: ReactNode;
	/** Línea superior pequeña (tipo, exchange…). */
	eyebrow?: ReactNode;
	/** Contenido extra al pie (badges, avisos). */
	footer?: ReactNode;
	disabled?: boolean;
	className?: string;
};

/** Opción seleccionable en forma de tarjeta para los pasos del asistente. */
export function ChoiceCard({
	selected,
	onSelect,
	title,
	description,
	eyebrow,
	footer,
	disabled,
	className,
}: ChoiceCardProps) {
	return (
		<button
			type="button"
			aria-pressed={selected}
			disabled={disabled}
			onClick={onSelect}
			className={cn(
				'relative flex h-full flex-col gap-1.5 rounded-xl border bg-card p-4 text-left transition-all',
				'hover:border-primary/50 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50',
				'disabled:cursor-not-allowed disabled:opacity-50',
				selected && 'border-primary bg-primary/5 ring-1 ring-primary',
				className,
			)}
		>
			{selected && (
				<IconCircleCheckFilled className="absolute top-3 right-3 size-5 text-primary" />
			)}
			{eyebrow && (
				<span className="pr-6 text-xs text-muted-foreground">{eyebrow}</span>
			)}
			<span className="pr-6 font-semibold">{title}</span>
			{description && (
				<span className="text-sm text-muted-foreground">{description}</span>
			)}
			{footer && <span className="mt-auto pt-2">{footer}</span>}
		</button>
	);
}
