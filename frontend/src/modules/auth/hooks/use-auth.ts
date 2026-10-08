import { useContext } from 'react';
import type { AuthContextValue } from '@/modules/auth/context/auth-context';
import { AuthContext } from '@/modules/auth/context/auth-context';

export function useAuth(): AuthContextValue {
	const context = useContext(AuthContext);
	if (!context) {
		throw new Error('useAuth debe usarse dentro de <AuthProvider>');
	}
	return context;
}
