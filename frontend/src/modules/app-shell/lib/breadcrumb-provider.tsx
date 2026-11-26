import { type ReactNode, useState } from 'react';
import type { BreadcrumbEntry } from '@/modules/app-shell/lib/breadcrumb-context';
import { BreadcrumbContext } from '@/modules/app-shell/lib/breadcrumb-context';

export function BreadcrumbProvider({ children }: { children: ReactNode }) {
	const [items, setItems] = useState<BreadcrumbEntry[]>([]);

	return (
		<BreadcrumbContext.Provider value={{ items, setItems }}>
			{children}
		</BreadcrumbContext.Provider>
	);
}
