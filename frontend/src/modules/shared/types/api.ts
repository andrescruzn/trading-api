/**
 * Envelope que devuelve toda la API (ver skill `api-standards` del backend):
 * `errorCode` es el HTTP status real (200/201 en éxito, >= 400 en error) y
 * `msg` ya es texto de interfaz (`error_messages.py`), listo para mostrar.
 */
type ApiEnvelope<T> = {
	msg: string;
	errorCode: number;
	data: T;
};

/** Forma de `build_paginated_response` del backend. */
type Paginated<T> = {
	items: T[];
	pagination: {
		total: number;
		page: number;
		page_size: number;
		total_pages: number;
	};
};

const PAGE_LIMIT_OPTIONS = [10, 20, 50, 100] as const;
type PageLimit = (typeof PAGE_LIMIT_OPTIONS)[number];
const DEFAULT_PAGE_LIMIT: PageLimit = 20;

export type { ApiEnvelope, PageLimit, Paginated };
export { DEFAULT_PAGE_LIMIT, PAGE_LIMIT_OPTIONS };
