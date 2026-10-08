import { dispatchSessionCleared } from '@/modules/auth/lib/auth-bridge';
import { useSessionExpiredStore } from '@/modules/auth/lib/session-expired-store';
import type { ApiEnvelope } from '@/modules/shared/types/api';

const API_URL = import.meta.env.VITE_API_URL ?? '/api';

// Rutas de auth cuyo 401 es parte del propio flujo (credenciales malas, OTP
// vencido…): nunca deben cerrar la sesión ni redirigir a `/login`.
const AUTH_FLOW_PATHS = [
	'/users/login',
	'/users/login/otp/verify',
	'/users/logout',
];

// Chequeo de arranque: un 401 aquí solo significa "no hay sesión", no que
// una sesión haya expirado — no se muestra el aviso.
const ME_PATH = '/users/me';

const NETWORK_ERROR_MESSAGE =
	'No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.';

class ApiClientError extends Error {
	status: number;
	data: unknown;

	constructor(message: string, status: number, data?: unknown) {
		super(message);
		this.name = 'ApiClientError';
		this.status = status;
		this.data = data;
	}
}

type QueryParams = Record<string, string | number | boolean | null | undefined>;

/** Arma `?a=1&b=2` omitiendo valores vacíos (`undefined`, `null`, `''`). */
function buildQuery(params?: QueryParams): string {
	if (!params) return '';
	const search = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value === undefined || value === null || value === '') continue;
		search.set(key, String(value));
	}
	const query = search.toString();
	return query ? `?${query}` : '';
}

async function rawFetch(path: string, options: RequestInit): Promise<Response> {
	// Con `FormData` el navegador fija `Content-Type: multipart/form-data` con su
	// `boundary`; forzar JSON acá rompería la subida de archivos.
	const isJsonBody = !!options.body && !(options.body instanceof FormData);

	return fetch(`${API_URL}${path}`, {
		...options,
		// La sesión vive en una cookie HttpOnly: el JS nunca ve el token.
		credentials: 'include',
		headers: {
			Accept: 'application/json',
			...(isJsonBody && { 'Content-Type': 'application/json' }),
			...options.headers,
		},
	});
}

async function parseBody<T>(
	response: Response,
): Promise<ApiEnvelope<T> | null> {
	if (response.status === 204) {
		return { msg: '', errorCode: 204, data: null as T };
	}
	try {
		return (await response.json()) as ApiEnvelope<T>;
	} catch {
		return null;
	}
}

async function toResult<T>(response: Response): Promise<ApiEnvelope<T>> {
	const body = await parseBody<T>(response);
	const status = body?.errorCode ?? response.status;

	// El backend marca el error con `errorCode >= 400`; `!response.ok` cubre
	// respuestas que no vienen del envelope (proxy caído, 502 del servidor…).
	if (!response.ok || !body || status >= 400) {
		throw new ApiClientError(
			body?.msg || NETWORK_ERROR_MESSAGE,
			status,
			body?.data,
		);
	}
	return body;
}

/**
 * Cierra la sesión local y redirige a `/login`. `announce` marca que fue un
 * cierre forzado (para que `/login` muestre el aviso de sesión vencida).
 */
async function endSession(announce: boolean) {
	if (announce) {
		useSessionExpiredStore.getState().announceSessionExpired();
	}

	// Import dinámico: `router` depende (transitivamente) de este módulo (vía
	// `auth-context` -> rutas -> layouts -> `router`), así que importarlo de
	// forma estática crearía un ciclo de módulos.
	dispatchSessionCleared();
	const { router } = await import('@/router');
	router.navigate({ to: '/login' });
}

/**
 * Todo el tráfico a la API pasa por acá. El backend no tiene refresh token:
 * un 401 fuera del flujo de login significa que la cookie venció o que la
 * sesión se revocó (cada login rota el `jti`), así que se cierra la sesión y
 * se vuelve a `/login` con el aviso de "sesión expirada". El 401 de
 * `GET /users/me` al arrancar solo significa "no hay sesión": sin aviso.
 */
async function apiFetchFull<T>(
	path: string,
	options: RequestInit = {},
): Promise<ApiEnvelope<T>> {
	let response: Response;
	try {
		response = await rawFetch(path, options);
	} catch {
		throw new ApiClientError(NETWORK_ERROR_MESSAGE, 0);
	}

	if (
		response.status === 401 &&
		!AUTH_FLOW_PATHS.includes(path) &&
		path !== ME_PATH
	) {
		await endSession(true);
	}

	return toResult<T>(response);
}

async function apiFetch<T>(
	path: string,
	options: RequestInit = {},
): Promise<T> {
	const { data } = await apiFetchFull<T>(path, options);
	return data;
}

/** Atajos por verbo. `body` se serializa a JSON; `params` va como query string. */
const api = {
	get: <T>(path: string, params?: QueryParams) =>
		apiFetch<T>(`${path}${buildQuery(params)}`),
	post: <T>(path: string, body?: unknown) =>
		apiFetch<T>(path, {
			method: 'POST',
			body: body === undefined ? undefined : JSON.stringify(body),
		}),
	put: <T>(path: string, body: unknown) =>
		apiFetch<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
	patch: <T>(path: string, body: unknown) =>
		apiFetch<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
	delete: <T>(path: string) => apiFetch<T>(path, { method: 'DELETE' }),
};

export type { QueryParams };
export { ApiClientError, api, apiFetch, apiFetchFull, buildQuery };
