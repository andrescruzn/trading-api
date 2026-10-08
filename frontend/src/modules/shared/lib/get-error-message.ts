import { ApiClientError } from '@/modules/shared/lib/api-client';

const DEFAULT_ERROR_DESCRIPTION = 'Revisa tu conexión e inténtalo de nuevo.';

/**
 * Texto para mostrar al usuario cuando falla una petición: el `message` de la
 * API (ya redactado como texto de interfaz) o, si el error no vino de la API
 * (red caída, etc.), el `fallback` o el mensaje de conexión por defecto.
 */
function getErrorMessage(
	error: unknown,
	fallback: string = DEFAULT_ERROR_DESCRIPTION,
): string {
	return error instanceof ApiClientError ? error.message : fallback;
}

export { DEFAULT_ERROR_DESCRIPTION, getErrorMessage };
