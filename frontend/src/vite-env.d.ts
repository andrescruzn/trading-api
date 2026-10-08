/// <reference types="vite/client" />

interface ImportMetaEnv {
	/** URL completa de la API REST (p. ej. `http://localhost:8000/api`). */
	readonly VITE_API_URL: string;
}

interface ImportMeta {
	readonly env: ImportMetaEnv;
}
