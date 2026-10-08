/// <reference types="vite/client" />

interface ImportMetaEnv {
	/** Base de la API REST (p. ej. `/api` en desarrollo, vía proxy de Vite). */
	readonly VITE_API_URL: string;
	/** Solo desarrollo: destino del proxy `/api` de Vite. */
	readonly VITE_API_PROXY_TARGET?: string;
}

interface ImportMeta {
	readonly env: ImportMetaEnv;
}
