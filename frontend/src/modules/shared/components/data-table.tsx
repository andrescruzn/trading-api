import { type ReactNode, useEffect } from 'react';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { TablePagination } from '@/modules/shared/components/table-pagination';
import { useClientPagination } from '@/modules/shared/hooks/use-client-pagination';
import { PAGE_LIMIT_OPTIONS, type PageLimit } from '@/modules/shared/types/api';
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

export type DataTableColumn<T> = {
	/** Clave única de la columna (también sirve de `key` de React). */
	id: string;
	header: ReactNode;
	cell: (row: T) => ReactNode;
	/** Clases para `<th>` y `<td>` (p. ej. `text-right`, `font-mono`). */
	className?: string;
	/** Ancho del skeleton mientras carga (clase Tailwind, p. ej. `w-24`). */
	skeletonClassName?: string;
};

/**
 * Paginación controlada (en el servidor): `rows` ya es la página actual y
 * `total`/`totalPages` vienen de la respuesta `{items, pagination}`. Se arma
 * con `useServerPagination`.
 */
export type ServerPagination = {
	page: number;
	pageSize: PageLimit;
	total: number;
	totalPages: number;
	onPageChange: (page: number) => void;
	onPageSizeChange: (pageSize: PageLimit) => void;
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
	/** Si se pasa, la paginación es del servidor y `paginate` se ignora. */
	pagination?: ServerPagination;
	/** Hay una página nueva en camino (se ve la anterior atenuada). */
	isFetching?: boolean;
	skeletonRows?: number;
	className?: string;
};

/**
 * Tabla estándar de listados: skeleton mientras carga, error inline, estado
 * vacío y paginación en el navegador o, con `pagination`, en el servidor
 * (página a página). Las columnas se declaran como datos
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
	pagination: serverPagination,
	isFetching = false,
	skeletonRows = 5,
	className,
}: DataTableProps<T>) {
	const allRows = rows ?? [];
	const clientPagination = useClientPagination(allRows);
	const isServer = serverPagination !== undefined;
	const visibleRows =
		paginate && !isServer ? clientPagination.pageItems : allRows;

	// Si la página actual se quedó sin filas (p. ej. cambió el total), vuelve
	// a la última que existe.
	const serverPage = serverPagination?.page ?? 1;
	const serverTotalPages = serverPagination?.totalPages ?? 0;
	const onServerPageChange = serverPagination?.onPageChange;
	useEffect(() => {
		if (!isLoading && serverTotalPages > 0 && serverPage > serverTotalPages)
			onServerPageChange?.(serverTotalPages);
	}, [isLoading, serverPage, serverTotalPages, onServerPageChange]);

	if (error) {
		return <ErrorAlert title={errorTitle} error={error} />;
	}

	const showHeader = isLoading || allRows.length > 0;

	return (
		<div
			className={cn('flex flex-col gap-4', className)}
			aria-busy={isFetching || isLoading}
		>
			<Table
				className={cn(
					'transition-opacity',
					isFetching && !isLoading && 'opacity-60',
				)}
			>
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
			{isServer
				? !isLoading &&
					// Visible desde el tamaño más chico para poder volver a él.
					serverPagination.total > PAGE_LIMIT_OPTIONS[0] && (
						<TablePagination
							page={serverPagination.page}
							limit={serverPagination.pageSize}
							total={serverPagination.total}
							totalPages={serverPagination.totalPages}
							onPageChange={serverPagination.onPageChange}
							onLimitChange={serverPagination.onPageSizeChange}
						/>
					)
				: paginate &&
					!isLoading &&
					clientPagination.total > clientPagination.limit && (
						<TablePagination
							page={clientPagination.page}
							limit={clientPagination.limit}
							total={clientPagination.total}
							totalPages={clientPagination.totalPages}
							onPageChange={clientPagination.setPage}
							onLimitChange={clientPagination.setLimit}
						/>
					)}
		</div>
	);
}
