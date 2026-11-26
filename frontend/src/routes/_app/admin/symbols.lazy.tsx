import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminSymbolsPage } from '@/modules/market/pages/admin-symbols';

export const Route = createLazyFileRoute('/_app/admin/symbols')({
	component: AdminSymbolsPage,
});
