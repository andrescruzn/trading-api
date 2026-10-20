import { createLazyFileRoute } from '@tanstack/react-router';
import { AdminAuditPage } from '@/modules/auth/pages/admin-audit';

export const Route = createLazyFileRoute('/_app/admin/audit')({
	component: AdminAuditPage,
});
