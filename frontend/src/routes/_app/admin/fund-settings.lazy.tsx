import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminFundSettingsPage } from '@/modules/fund/pages/admin-fund-settings';

export const Route = createLazyFileRoute('/_app/admin/fund-settings')({
	component: AdminFundSettingsPage,
});
