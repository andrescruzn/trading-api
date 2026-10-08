import { create } from 'zustand';

type SessionExpiredState = {
	visible: boolean;
	/**
	 * Marca que la sesión se cerró por un 401 de la API (no un logout
	 * manual) — `api-client.ts` lo llama justo antes de redirigir a `/login`,
	 * fuera de React (vía `useSessionExpiredStore.getState()`).
	 * `SessionExpiredDialog` lee `visible` para mostrar un aviso y lo
	 * reconoce (`acknowledgeSessionExpired`) al cerrarse, para que no
	 * reaparezca en visitas posteriores a `/login`.
	 */
	announceSessionExpired: () => void;
	acknowledgeSessionExpired: () => void;
};

const useSessionExpiredStore = create<SessionExpiredState>((set, get) => ({
	visible: false,
	announceSessionExpired: () => set({ visible: true }),
	acknowledgeSessionExpired: () => {
		if (!get().visible) return;
		set({ visible: false });
	},
}));

export { useSessionExpiredStore };
