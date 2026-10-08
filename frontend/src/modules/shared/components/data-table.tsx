import type { ReactNode } from 'react';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { TablePagination } from '@/modules/shared/components/table-pagination';
import { useClientPagination } from '@/modules/shared/hooks/use-client-pagination';
import { Skeleton } from '@/modules/ui/components/skeleton';
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from '@/modules/ui/components/table';
import { cn } from '@/modules/ui/lib/utils';

type DataTableColumn<T> = {
	/** Clave única de la columna (también sirve de `key` de React). */
	id: string;
	header: ReactNode;
	cell: (row: T) => ReactNode;
	/** Clases para `<th>` y `<td>` (p. ej. `text-right`, `font-mono`). */
	className?: string;
	/** Ancho del skeleton mientras carga (clase Tailwind, p. ej. `w-24`). */
	skeletonClassName?: string;
};

type DataTableProps<T> = {
	columns: DataTableColumn<T>[];
	rows: T[] | undefined;
	getRowId: (row: T) => string | number;
	isLoading: boolean;
	error?: unknown;
	/** Ej. `No pudimos cargar los símbolos`. */
	errorTitle?: string;
	/** Texto o nodo cuando no hay filas (puede incluir un CTA). */
	empty: ReactNode;
	/** Fila clicable (abre detalle). Las celdas con acciones deben frenar la propagación. */
	onRowClick?: (row: T) => void;
	/** Pagina en el navegador. `false` para listas cortas o ya limitadas por la API. */
	paginate?: boolean;
	skeletonRows?: number;
	className?: string;
};

/**
 * Tabla estándar de listados: skeleton mientras carga, error inline, estado
 * vacío y paginación en el navegador. Las columnas se declaran como datos
 * (`DataTableColumn<T>[]`) en la página; la columna de acciones es una
 * columna más cuyo `cell` renderiza un `DropdownMenu`.
 */
export function DataTable<T>({
	columns,
	rows,
	getRowId,
	isLoading,
	error,
	errorTitle = 'No pudimos cargar la información',
	empty,
	onRowClick,
	paginate = true,
	skeletonRows = 5,
	className,
}: DataTableProps<T>) {
	const allRows = rows ?? [];
	const pagination = useClientPagination(allRows);
	const visibleRows = paginate ? pagination.pageItems : allRows;

	if (error) {
		return <ErrorAlert title={errorTitle} error={error} />;
	}

	const showHeader = isLoading || allRows.length > 0;

	return (
		<div className={cn('flex flex-col gap-4', className)}>
			<Table>
				{showHeader && (
					<TableHeader>
						<TableRow>
							{columns.map((column) => (
								<TableHead key={column.id} className={column.className}>
									{column.header}
								</TableHead>
							))}
						</TableRow>
					</TableHeader>
				)}
				<TableBody>
					{isLoading ? (
						Array.from({ length: skeletonRows }, (_, index) => (
							<TableRow key={index}>
								{columns.map((column) => (
									<TableCell key={column.id} className={column.className}>
										<Skeleton
											className={cn('h-4 w-20', column.skeletonClassName)}
										/>
									</TableCell>
								))}
							</TableRow>
						))
					) : allRows.length === 0 ? (
						<TableRow>
							<TableCell
								colSpan={columns.length}
								className="py-10 text-center whitespace-normal text-muted-foreground"
							>
								{empty}
							</TableCell>
						</TableRow>
					) : (
						visibleRows.map((row) => (
							<TableRow
								key={getRowId(row)}
								className={onRowClick ? 'cursor-pointer' : undefined}
								onClick={onRowClick ? () => onRowClick(row) : undefined}
							>
								{columns.map((column) => (
									<TableCell key={column.id} className={column.className}>
										{column.cell(row)}
									</TableCell>
								))}
							</TableRow>
						))
					)}
				</TableBody>
			</Table>
			{paginate && !isLoading && pagination.total > pagination.limit && (
				<TablePagination
					page={pagination.page}
					limit={pagination.limit}
					total={pagination.total}
					totalPages={pagination.totalPages}
					onPageChange={pagination.setPage}
					onLimitChange={pagination.setLimit}
				/>
			)}
		</div>
	);
}

export type { DataTableColumn };
