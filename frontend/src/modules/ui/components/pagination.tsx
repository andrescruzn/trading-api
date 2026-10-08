import {
	IconChevronLeft,
	IconChevronRight,
	IconDots,
} from '@tabler/icons-react';
import { cn } from '@/modules/ui/lib/utils';
import type * as React from 'react';
import { Button } from '@/modules/ui/components/button';

function Pagination({ className, ...props }: React.ComponentProps<'nav'>) {
	return (
		<nav
			aria-label="Paginación"
			data-slot="pagination"
			className={cn('mx-auto flex w-full justify-center', className)}
			{...props}
		/>
	);
}

function PaginationContent({
	className,
	...props
}: React.ComponentProps<'ul'>) {
	return (
		<ul
			data-slot="pagination-content"
			className={cn('flex items-center gap-1', className)}
			{...props}
		/>
	);
}

function PaginationItem({ ...props }: React.ComponentProps<'li'>) {
	return <li data-slot="pagination-item" {...props} />;
}

type PaginationLinkProps = {
	isActive?: boolean;
} & Pick<React.ComponentProps<typeof Button>, 'size'> &
	React.ComponentProps<'a'>;

function PaginationLink({
	className,
	isActive,
	size = 'icon-sm',
	...props
}: PaginationLinkProps) {
	return (
		<Button
			variant={isActive ? 'outline' : 'ghost'}
			size={size}
			className={cn(className)}
			nativeButton={false}
			render={
				<a
					aria-current={isActive ? 'page' : undefined}
					data-slot="pagination-link"
					data-active={isActive}
					{...props}
				/>
			}
		/>
	);
}

function PaginationPrevious({
	className,
	text = 'Anterior',
	...props
}: React.ComponentProps<typeof PaginationLink> & { text?: string }) {
	return (
		<PaginationLink
			aria-label="Ir a la página anterior"
			size="default"
			className={cn('pl-2!', className)}
			{...props}
		>
			<IconChevronLeft data-icon="inline-start" />
			<span className="hidden sm:block">{text}</span>
		</PaginationLink>
	);
}

function PaginationNext({
	className,
	text = 'Siguiente',
	...props
}: React.ComponentProps<typeof PaginationLink> & { text?: string }) {
	return (
		<PaginationLink
			aria-label="Ir a la página siguiente"
			size="default"
			className={cn('pr-2!', className)}
			{...props}
		>
			<span className="hidden sm:block">{text}</span>
			<IconChevronRight data-icon="inline-end" />
		</PaginationLink>
	);
}

function PaginationEllipsis({
	className,
	...props
}: React.ComponentProps<'span'>) {
	return (
		<span
			aria-hidden
			data-slot="pagination-ellipsis"
			className={cn(
				"flex size-9 items-center justify-center [&_svg:not([class*='size-'])]:size-4",
				className,
			)}
			{...props}
		>
			<IconDots />
			<span className="sr-only">Más páginas</span>
		</span>
	);
}

export {
	Pagination,
	PaginationContent,
	PaginationEllipsis,
	PaginationItem,
	PaginationLink,
	PaginationNext,
	PaginationPrevious,
};
