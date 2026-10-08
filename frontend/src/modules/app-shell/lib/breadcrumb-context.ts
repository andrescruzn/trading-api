import { createContext } from 'react';

export interface BreadcrumbEntry {
	label: string;
	href?: string;
}

export interface BreadcrumbContextValue {
	items: BreadcrumbEntry[];
	setItems: (items: BreadcrumbEntry[]) => void;
}

// Exportado (no solo interno) para que `breadcrumb-provider.tsx` y
// `use-breadcrumb-context.ts` lo consuman: mantener el objeto de contexto
// separado del componente y del hook evita que un guardado en cualquier
// punto de la app recree el Context mientras el Provider ya montado sigue
// referenciando el anterior (ver el mismo patrón en `auth-context.ts`).
export const BreadcrumbContext = createContext<BreadcrumbContextValue | null>(
	null,
);
