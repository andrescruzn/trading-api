import { useContext } from 'react';
import type { BreadcrumbContextValue } from '@/modules/app-shell/lib/breadcrumb-context';
import { BreadcrumbContext } from '@/modules/app-shell/lib/breadcrumb-context';

export function useBreadcrumbContext(): BreadcrumbContextValue {
	const context = useContext(BreadcrumbContext);
	if (!context) {
		throw new Error(
			'useBreadcrumbContext debe usarse dentro de un BreadcrumbProvider',
		);
	}
	return context;
}
