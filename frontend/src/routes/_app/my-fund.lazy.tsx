import { createLazyFileRoute } from '@tanstack/react-router';
import { MyFundPage } from '@/modules/fund/pages/my-fund';

export const Route = createLazyFileRoute('/_app/my-fund')({
	component: MyFundPage,
});
