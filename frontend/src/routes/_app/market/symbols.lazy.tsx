import { createLazyFileRoute } from '@tanstack/react-router';
import { SymbolsPage } from '@/modules/market/pages/symbols';

export const Route = createLazyFileRoute('/_app/market/symbols')({
	component: SymbolsPage,
});
