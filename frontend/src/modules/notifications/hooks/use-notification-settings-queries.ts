import { useQuery } from '@tanstack/react-query';
import { getNotificationSettings } from '@/modules/notifications/api/notification-settings.api';

const NOTIFICATION_SETTINGS_QUERY_KEY = ['notification-settings'] as const;

function useNotificationSettingsQuery() {
	return useQuery({
		queryKey: NOTIFICATION_SETTINGS_QUERY_KEY,
		queryFn: getNotificationSettings,
	});
}

export { NOTIFICATION_SETTINGS_QUERY_KEY, useNotificationSettingsQuery };
