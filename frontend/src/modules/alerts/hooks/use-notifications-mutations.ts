import { useMutation, useQueryClient } from '@tanstack/react-query';
import { markNotificationsSeen } from '@/modules/alerts/api/notifications.api';
import { NOTIFICATIONS_QUERY_KEY } from '@/modules/alerts/hooks/use-notifications-queries';

function useMarkNotificationsSeenMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: markNotificationsSeen,
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_QUERY_KEY }),
	});
}

export { useMarkNotificationsSeenMutation };
