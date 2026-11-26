import { createHashHistory, createRouter } from '@tanstack/react-router';
import { PendingPage } from '@/modules/shared/components/pending-page';
import { routeTree } from './routeTree.gen';

const hashHistory = createHashHistory();

export const router = createRouter({
	routeTree,
	history: hashHistory,
	defaultPendingComponent: PendingPage,
});

declare module '@tanstack/react-router' {
	interface Register {
		router: typeof router;
	}
}
