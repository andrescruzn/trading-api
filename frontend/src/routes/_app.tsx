import { createFileRoute } from '@tanstack/react-router';
import { AppNotFoundPage } from '@/modules/app-shell/components/app-not-found-page';
import { AppShellLayout } from '@/modules/app-shell/layouts/app-shell';

export const Route = createFileRoute('/_app')({
	component: AppShellLayout,
	notFoundComponent: AppNotFoundPage,
});
