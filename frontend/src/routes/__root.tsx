import { createRootRoute } from '@tanstack/react-router';
import { ErrorPage } from '@/modules/shared/components/error-page';
import { NotFoundPage } from '@/modules/shared/components/not-found-page';
import { MainLayout } from '@/modules/shared/layouts/main';

export const Route = createRootRoute({
	component: MainLayout,
	errorComponent: ErrorPage,
	notFoundComponent: NotFoundPage,
});
