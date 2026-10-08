import { useEffect } from 'react';
import { useBreadcrumbContext } from '@/modules/app-shell/hooks/use-breadcrumb-context';
import type { BreadcrumbEntry } from '@/modules/app-shell/lib/breadcrumb-context';

export function usePageBreadcrumb(items: BreadcrumbEntry[]) {
	const { setItems } = useBreadcrumbContext();
	const key = items.map((item) => `${item.label}:${item.href ?? ''}`).join('|');

	useEffect(() => {
		setItems(items);
		return () => setItems([]);
	}, [key]);
}
