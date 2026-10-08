import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { parseEnv } from 'node:util';
import tailwindcss from '@tailwindcss/vite';
import { tanstackRouter } from '@tanstack/router-plugin/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const ROOT_DIR = import.meta.dirname;
const FRONTEND_DIR = path.resolve(ROOT_DIR, 'frontend');

// El front lee sus variables de `.env_frontend` (raíz del repo), no del `.env`
// del backend. Vite expone al cliente las `VITE_*` que encuentre en
// `process.env`, así que basta con volcarlas antes de definir la config.
const ENV_FILE = path.resolve(ROOT_DIR, '.env_frontend');
if (existsSync(ENV_FILE)) {
	const parsed = parseEnv(readFileSync(ENV_FILE, 'utf8'));
	for (const [key, value] of Object.entries(parsed)) {
		process.env[key] ??= value;
	}
}

const API_PROXY_TARGET =
	process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000';

// https://vite.dev/config/
export default defineConfig({
	root: FRONTEND_DIR,
	// `envDir` dentro de `frontend/` para que Vite no cargue el `.env` del backend.
	envDir: FRONTEND_DIR,
	build: {
		outDir: 'dist',
		emptyOutDir: true,
	},
	server: {
		// En desarrollo el front y la API comparten origen (proxy), así la cookie
		// HttpOnly `SameSite=Lax` viaja sin configurar CORS ni HTTPS.
		proxy: {
			'/api': { target: API_PROXY_TARGET, changeOrigin: true },
		},
	},
	plugins: [
		tanstackRouter({
			target: 'react',
			autoCodeSplitting: true,
			routesDirectory: path.resolve(FRONTEND_DIR, 'src/routes'),
			generatedRouteTree: path.resolve(FRONTEND_DIR, 'src/routeTree.gen.ts'),
		}),
		react(),
		tailwindcss(),
	],
	resolve: {
		alias: {
			'@': path.resolve(FRONTEND_DIR, 'src'),
		},
	},
});
