import { useEffect, useMemo, useState } from 'react';
import {
	DEFAULT_PAGE_LIMIT,
	type PageLimit,
} from '@/modules/shared/types/api';

/**
 * Paginación en el navegador para listas que el backend devuelve completas
 * (hoy ningún endpoint pagina en servidor). Vuelve a la página 1 cuando
 * cambia el total (p. ej. al aplicar un filtro).
 */
function useClientPagination<T>(items: T[], initialLimit = DEFAULT_PAGE_LIMIT) {
	const [page, setPage] = useState(1);
	const [limit, setLimit] = useState<PageLimit>(initialLimit);

	const total = items.length;
	const totalPages = Math.max(Math.ceil(total / limit), 1);

	useEffect(() => {
		setPage(1);
	}, [total]);

	const pageItems = useMemo(
		() => items.slice((page - 1) * limit, page * limit),
		[items, page, limit],
	);

	return {
		page: Math.min(page, totalPages),
		limit,
		total,
		totalPages,
		pageItems,
		setPage,
		setLimit: (next: PageLimit) => {
			setLimit(next);
			setPage(1);
		},
	};
}

export { useClientPagination };
