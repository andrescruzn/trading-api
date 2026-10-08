import { createLazyFileRoute } from '@tanstack/react-router';
import { PortfolioPage } from '@/modules/accounts/pages/portfolio';

export const Route = createLazyFileRoute('/_app/portfolio')({
	component: PortfolioPage,
});
