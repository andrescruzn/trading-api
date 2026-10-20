import { useState } from 'react';
import type { ServerPagination } from '@/modules/shared/components/data-table';
import {
	DEFAULT_PAGE_LIMIT,
	type PageLimit,
	type PageParams,
	type Paginated,
} from '@/modules/shared/types/api';

/**
 * Estado de un listado paginado en el servidor: página y tamaño que viajan a
 * la API (`params`, para la query key y la llamada) y el objeto que espera
 * `DataTable` en su prop `pagination`.
 *
 * `resetKey` resume los filtros activos (p. ej. `JSON.stringify(filters)`):
 * si cambia, vuelve a la página 1 en el mismo render, sin pedir antes la
 * página vieja con los filtros nuevos.
 */
function useServerPagination(
	resetKey: string,
	initialPageSize: PageLimit = DEFAULT_PAGE_LIMIT,
) {
	const [page, setPage] = useState(1);
	const [pageSize, setPageSize] = useState<PageLimit>(initialPageSize);
	const [lastResetKey, setLastResetKey] = useState(resetKey);

	let currentPage = page;
	if (resetKey !== lastResetKey) {
		setLastResetKey(resetKey);
		setPage(1);
		currentPage = 1;
	}

	const params: PageParams = { page: currentPage, page_size: pageSize };

	/** Props de paginación para `DataTable` a partir de la respuesta. */
	function tablePagination(
		data: Paginated<unknown> | undefined,
	): ServerPagination {
		return {
			page: currentPage,
			pageSize,
			total: data?.pagination.total ?? 0,
			totalPages: data?.pagination.total_pages ?? 0,
			onPageChange: setPage,
			onPageSizeChange: (next) => {
				setPageSize(next);
				setPage(1);
			},
		};
	}

	return { params, tablePagination };
}

export { useServerPagination };
