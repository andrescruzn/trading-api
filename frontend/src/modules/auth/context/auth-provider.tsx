import {
	type ReactNode,
	useCallback,
	useEffect,
	useRef,
	useState,
} from 'react';
import type { CurrentUser } from '@/modules/auth/api/auth.api';
import { me as fetchCurrentUser } from '@/modules/auth/api/auth.api';
import type {
	AuthContextValue,
	AuthState,
} from '@/modules/auth/context/auth-context';
import { AuthContext } from '@/modules/auth/context/auth-context';
import { onSessionCleared } from '@/modules/auth/lib/auth-bridge';
import { ApiClientError } from '@/modules/shared/lib/api-client';

const PROFILE_REFRESH_MS = 5 * 60 * 1000;

function AuthProvider({ children }: { children: ReactNode }) {
	const [state, setState] = useState<AuthState>({ status: 'idle', user: null });
	// `ensureLoaded()` necesita leer/comparar el estado más reciente de forma
	// síncrona dentro de sus callbacks async (p. ej. para descartar una
	// respuesta obsoleta), sin esperar a que un re-render actualice el closure
	// de `state` — por eso se lleva en paralelo en un ref.
	const stateRef = useRef(state);
	const pendingRef = useRef<Promise<void> | null>(null);

	const setAndTrack = useCallback((next: AuthState) => {
		stateRef.current = next;
		setState(next);
	}, []);

	const setAuthenticated = useCallback(
		(user: CurrentUser) => {
			pendingRef.current = null;
			setAndTrack({ status: 'authenticated', user });
		},
		[setAndTrack],
	);

	const clear = useCallback(() => {
		pendingRef.current = null;
		setAndTrack({ status: 'unauthenticated', user: null });
	}, [setAndTrack]);

	// Vuelve a pedir `/users/me` para refrescar datos del usuario ya
	// autenticado (o cargarlos justo después del login, que solo pone la cookie) — a diferencia de
	// `ensureLoaded`, no le importa el estado previo ni evita pedidos en
	// paralelo: se usa puntualmente después de una acción que cambió esos
	// datos.
	const refreshUser = useCallback(async () => {
		try {
			const user = await fetchCurrentUser();
			setAndTrack({ status: 'authenticated', user });
		} catch (error) {
			if (!(error instanceof ApiClientError)) throw error;
			setAndTrack({ status: 'unauthenticated', user: null });
		}
	}, [setAndTrack]);

	// `api-client.ts` corre fuera del árbol de React (es un interceptor de
	// fetch) y necesita poder limpiar la sesión cuando la API responde 401.
	useEffect(() => onSessionCleared(clear), [clear]);

	// Si un admin cambia el rol (o el nombre) de la persona, el menú se
	// actualiza solo: se relee `/users/me` cada pocos minutos y al volver a
	// la pestaña. Un fallo aquí no cierra la sesión: de eso se encarga el 401
	// de la siguiente acción real (con su aviso).
	const isAuthenticated = state.status === 'authenticated';
	useEffect(() => {
		if (!isAuthenticated) return;
		const refresh = () => {
			fetchCurrentUser()
				.then((user) => {
					if (stateRef.current.status === 'authenticated') {
						setAndTrack({ status: 'authenticated', user });
					}
				})
				.catch(() => {});
		};
		const onVisible = () => {
			if (document.visibilityState === 'visible') refresh();
		};
		const timer = window.setInterval(refresh, PROFILE_REFRESH_MS);
		document.addEventListener('visibilitychange', onVisible);
		return () => {
			window.clearInterval(timer);
			document.removeEventListener('visibilitychange', onVisible);
		};
	}, [isAuthenticated, setAndTrack]);

	const ensureLoaded = useCallback(async (): Promise<AuthState> => {
		if (
			stateRef.current.status === 'authenticated' ||
			stateRef.current.status === 'unauthenticated'
		) {
			return stateRef.current;
		}

		if (!pendingRef.current) {
			setAndTrack({ status: 'loading', user: null });
			pendingRef.current = fetchCurrentUser()
				.then((user) => {
					// Si mientras la petición estaba en vuelo algo más ya cambió el
					// estado (p. ej. un `setAuthenticated`/`clear` disparado desde
					// otro flujo), esta respuesta quedó obsoleta: no la apliques.
					if (stateRef.current.status !== 'loading') return;
					setAndTrack({ status: 'authenticated', user });
				})
				.catch((error) => {
					if (!(error instanceof ApiClientError)) throw error;
					if (stateRef.current.status !== 'loading') return;
					setAndTrack({ status: 'unauthenticated', user: null });
				})
				.finally(() => {
					pendingRef.current = null;
				});
		}

		await pendingRef.current;
		return stateRef.current;
	}, [setAndTrack]);

	const value: AuthContextValue = {
		...state,
		ensureLoaded,
		setAuthenticated,
		refreshUser,
		clear,
	};

	return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export { AuthProvider };
