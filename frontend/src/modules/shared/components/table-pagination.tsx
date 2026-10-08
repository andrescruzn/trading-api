import { PAGE_LIMIT_OPTIONS, type PageLimit } from '@/modules/shared/types/api';
import {
	Pagination,
	PaginationContent,
	PaginationEllipsis,
	PaginationItem,
	PaginationLink,
	PaginationNext,
	PaginationPrevious,
} from '@/modules/ui/components/pagination';
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from '@/modules/ui/components/select';
import { cn } from '@/modules/ui/lib/utils';

type TablePaginationProps = {
	page: number;
	limit: PageLimit;
	total: number;
	totalPages: number;
	onPageChange: (page: number) => void;
	onLimitChange: (limit: PageLimit) => void;
	className?: string;
};

const SIBLING_COUNT = 1;

function getPageItems(page: number, lastPage: number) {
	const items: Array<number | 'ellipsis'> = [1];

	const rangeStart = Math.max(2, page - SIBLING_COUNT);
	const rangeEnd = Math.min(lastPage - 1, page + SIBLING_COUNT);

	if (rangeStart > 2) items.push('ellipsis');
	for (let pageNumber = rangeStart; pageNumber <= rangeEnd; pageNumber++) {
		items.push(pageNumber);
	}
	if (rangeEnd < lastPage - 1) items.push('ellipsis');

	if (lastPage > 1) items.push(lastPage);

	return items;
}

function TablePagination({
	page,
	limit,
	total,
	totalPages,
	onPageChange,
	onLimitChange,
	className,
}: TablePaginationProps) {
	const lastPage = Math.max(totalPages, 1);
	const isFirstPage = page <= 1;
	const isLastPage = page >= lastPage;
	const from = total === 0 ? 0 : (page - 1) * limit + 1;
	const to = Math.min(page * limit, total);

	return (
		<div
			className={cn(
				'flex flex-col gap-x-3 gap-y-4 sm:flex-row sm:items-center sm:justify-between',
				className,
			)}
		>
			<Pagination className="mx-0 w-auto justify-center sm:justify-start">
				<PaginationContent>
					<PaginationItem>
						<PaginationPrevious
							href="#"
							aria-disabled={isFirstPage}
							tabIndex={isFirstPage ? -1 : undefined}
							className="aria-disabled:pointer-events-none aria-disabled:opacity-50"
							onClick={(event) => {
								event.preventDefault();
								if (!isFirstPage) onPageChange(page - 1);
							}}
						/>
					</PaginationItem>
					{getPageItems(page, lastPage).map((item, index) =>
						item === 'ellipsis' ? (
							<PaginationItem key={`ellipsis-${index}`}>
								<PaginationEllipsis />
							</PaginationItem>
						) : (
							<PaginationItem key={item}>
								<PaginationLink
									href="#"
									isActive={item === page}
									onClick={(event) => {
										event.preventDefault();
										if (item !== page) onPageChange(item);
									}}
								>
									{item}
								</PaginationLink>
							</PaginationItem>
						),
					)}
					<PaginationItem>
						<PaginationNext
							href="#"
							aria-disabled={isLastPage}
							tabIndex={isLastPage ? -1 : undefined}
							className="aria-disabled:pointer-events-none aria-disabled:opacity-50"
							onClick={(event) => {
								event.preventDefault();
								if (!isLastPage) onPageChange(page + 1);
							}}
						/>
					</PaginationItem>
				</PaginationContent>
			</Pagination>
			<div className="flex items-center gap-x-3 gap-y-4 justify-center sm:justify-end">
				<div className="text-sm whitespace-nowrap text-muted-foreground">
					<span>
						{total === 0
							? 'Sin resultados'
							: `Mostrando ${from}–${to} de ${total}`}
					</span>
				</div>
				<div className="flex items-center gap-2">
					<Select
						value={String(limit)}
						onValueChange={(value) => onLimitChange(Number(value) as PageLimit)}
						items={PAGE_LIMIT_OPTIONS.map((option) => ({
							value: String(option),
							label: String(option),
						}))}
					>
						<SelectTrigger size="sm" aria-label="Filas por página">
							<SelectValue />
						</SelectTrigger>
						<SelectContent alignItemWithTrigger={false}>
							{PAGE_LIMIT_OPTIONS.map((option) => (
								<SelectItem key={option} value={String(option)}>
									{option} por página
								</SelectItem>
							))}
						</SelectContent>
					</Select>
					<span className="hidden sm:inline-block text-sm whitespace-nowrap text-muted-foreground">
						por página
					</span>
				</div>
			</div>
		</div>
	);
}

export { TablePagination };
