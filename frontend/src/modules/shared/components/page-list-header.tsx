import { IconDots } from '@tabler/icons-react';
import type { VariantProps } from 'class-variance-authority';
import { type ReactElement, type ReactNode, useEffect, useState } from 'react';
import { Button, type buttonVariants } from '@/modules/ui/components/button';
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
} from '@/modules/ui/components/dropdown-menu';
import { cn } from '@/modules/ui/lib/utils';

type PageListHeaderBreakpoint = 'sm' | 'md' | 'lg' | 'xl';

export type PageListHeaderAction = {
	label: string;
	icon?: ReactNode;
	variant?: VariantProps<typeof buttonVariants>['variant'];
	onClick?: () => void;
	/** Para acciones de navegación: `render={<Link to="..." />}`. */
	render?: ReactElement;
	disabled?: boolean;
	/** Omite la acción sin tener que armar el arreglo con condicionales. */
	hidden?: boolean;
};

export type PageListHeaderProps = {
	title: ReactNode;
	description?: ReactNode;
	/** En orden de jerarquía: la primera es la principal (arriba en el menú, a la derecha en desktop). */
	actions?: PageListHeaderAction[];
	/** Desde este breakpoint las acciones se ven como botones; por debajo, en un menú "...". */
	breakpoint?: PageListHeaderBreakpoint;
	className?: string;
};

// Clases completas (no interpoladas) para que Tailwind las detecte.
const INLINE_ACTIONS_CLASSES: Record<PageListHeaderBreakpoint, string> = {
	sm: 'hidden sm:flex',
	md: 'hidden md:flex',
	lg: 'hidden lg:flex',
	xl: 'hidden xl:flex',
};

const MENU_ACTIONS_CLASSES: Record<PageListHeaderBreakpoint, string> = {
	sm: 'sm:hidden',
	md: 'md:hidden',
	lg: 'lg:hidden',
	xl: 'xl:hidden',
};

// Mismos valores por defecto de Tailwind v4 (en rem, como los evalúa el CSS).
const BREAKPOINT_MIN_WIDTH: Record<PageListHeaderBreakpoint, string> = {
	sm: '40rem',
	md: '48rem',
	lg: '64rem',
	xl: '80rem',
};

function ActionsMenu({
	actions,
	breakpoint,
}: {
	actions: PageListHeaderAction[];
	breakpoint: PageListHeaderBreakpoint;
}) {
	const [open, setOpen] = useState(false);

	// El popup vive en un portal fuera del contenedor que se oculta con CSS: sin esto,
	// abrir el menú en mobile y agrandar la ventana lo deja visible (y la página inerte).
	useEffect(() => {
		const query = window.matchMedia(
			`(min-width: ${BREAKPOINT_MIN_WIDTH[breakpoint]})`,
		);
		const closeOnDesktop = () => {
			if (query.matches) setOpen(false);
		};

		query.addEventListener('change', closeOnDesktop);
		return () => query.removeEventListener('change', closeOnDesktop);
	}, [breakpoint]);

	return (
		<DropdownMenu open={open} onOpenChange={setOpen}>
			<DropdownMenuTrigger render={<Button variant="outline" size="icon-sm" />}>
				<IconDots />
				<span className="sr-only">Acciones</span>
			</DropdownMenuTrigger>
			<DropdownMenuContent align="end" className="w-auto min-w-48">
				{actions.map((action) => (
					<DropdownMenuItem
						key={action.label}
						variant={
							action.variant === 'destructive' ? 'destructive' : 'default'
						}
						disabled={action.disabled}
						onClick={action.onClick}
						render={action.render}
					>
						{action.icon}
						{action.label}
					</DropdownMenuItem>
				))}
			</DropdownMenuContent>
		</DropdownMenu>
	);
}

function PageListHeader({
	title,
	description,
	actions = [],
	breakpoint = 'lg',
	className,
}: PageListHeaderProps) {
	const visibleActions = actions.filter((action) => !action.hidden);

	return (
		<div className={cn('flex items-center justify-between gap-x-6', className)}>
			<div className="min-w-0 flex-1">
				<h1 className="flex items-center gap-2 text-xl font-semibold">
					{title}
				</h1>
				{description && (
					<div className="text-sm text-muted-foreground">{description}</div>
				)}
			</div>

			{visibleActions.length > 0 && (
				<>
					<div
						className={cn(
							'shrink-0 flex-row-reverse items-center gap-2',
							INLINE_ACTIONS_CLASSES[breakpoint],
						)}
					>
						{visibleActions.map((action) => (
							<Button
								key={action.label}
								variant={action.variant}
								disabled={action.disabled}
								onClick={action.onClick}
								render={action.render}
							>
								{action.icon}
								{action.label}
							</Button>
						))}
					</div>

					<div className={cn('shrink-0', MENU_ACTIONS_CLASSES[breakpoint])}>
						<ActionsMenu actions={visibleActions} breakpoint={breakpoint} />
					</div>
				</>
			)}
		</div>
	);
}

export { PageListHeader };
