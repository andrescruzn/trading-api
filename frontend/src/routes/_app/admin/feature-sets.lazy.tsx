import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminFeatureSetsPage } from '@/modules/features/pages/admin-feature-sets';

export const Route = createLazyFileRoute('/_app/admin/feature-sets')({
	component: AdminFeatureSetsPage,
});
