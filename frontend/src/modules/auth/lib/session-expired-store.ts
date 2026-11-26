import { create } from 'zustand';

type SessionExpiredState = {
	visible: boolean;
	/** `msg` del 401 (p. ej. "iniciaste sesión en otro dispositivo"); null = genérico. */
	message: string | null;
	/**
	 * Marca que la sesión se cerró por un 401 de la API (no un logout
	 * manual) — `api-client.ts` lo llama justo antes de redirigir a `/login`,
	 * fuera de React (vía `useSessionExpiredStore.getState()`).
	 * `SessionExpiredDialog` lee `visible` para mostrar un aviso y lo
	 * reconoce (`acknowledgeSessionExpired`) al cerrarse, para que no
	 * reaparezca en visitas posteriores a `/login`.
	 */
	announceSessionExpired: (message?: string | null) => void;
	acknowledgeSessionExpired: () => void;
};

const useSessionExpiredStore = create<SessionExpiredState>((set, get) => ({
	visible: false,
	message: null,
	announceSessionExpired: (message = null) => set({ visible: true, message }),
	acknowledgeSessionExpired: () => {
		if (!get().visible) return;
		set({ visible: false, message: null });
	},
}));

export { useSessionExpiredStore };
