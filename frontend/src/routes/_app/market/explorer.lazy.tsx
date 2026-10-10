import { createLazyFileRoute } from '@tanstack/react-router';
import { ExplorerPage } from '@/modules/market/pages/explorer';

export const Route = createLazyFileRoute('/_app/market/explorer')({
	component: ExplorerPage,
});
