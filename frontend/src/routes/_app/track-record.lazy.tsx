import { createLazyFileRoute } from '@tanstack/react-router';
import { TrackRecordPage } from '@/modules/orders/pages/track-record';

export const Route = createLazyFileRoute('/_app/track-record')({
	component: TrackRecordPage,
});
