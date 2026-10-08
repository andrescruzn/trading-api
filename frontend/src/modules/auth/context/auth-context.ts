import { createContext } from 'react';
import type { CurrentUser } from '@/modules/auth/api/auth.api';

type AuthState =
	| { status: 'idle'; user: null }
	| { status: 'loading'; user: null }
	| { status: 'authenticated'; user: CurrentUser }
	| { status: 'unauthenticated'; user: null };

type AuthContextValue = AuthState & {
	ensureLoaded: () => Promise<AuthState>;
	setAuthenticated: (user: CurrentUser) => void;
	refreshUser: () => Promise<void>;
	clear: () => void;
};

// Este archivo no exporta ningún componente, solo el objeto de contexto y sus
// tipos: `auth-provider.tsx` (el componente) y `use-auth.ts` (el hook) lo
// consumen desde aquí. Mantenerlo así permite que ambos archivos sigan siendo
// límites válidos de Fast Refresh (solo exportan componentes/hooks, nunca
// mezclado con este objeto) y evita que un guardado en cualquier punto de la
// app termine recreando el Context mientras el Provider ya montado sigue
// referenciando el anterior.
export const AuthContext = createContext<AuthContextValue | null>(null);

export type { AuthContextValue, AuthState };
