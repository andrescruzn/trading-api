import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminTelegramPage } from '@/modules/alerts/pages/admin-telegram';

export const Route = createLazyFileRoute('/_app/admin/telegram')({
	component: AdminTelegramPage,
});
