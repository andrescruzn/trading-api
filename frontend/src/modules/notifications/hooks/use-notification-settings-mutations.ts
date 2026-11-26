import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	type NotificationSettings,
	sendEmailTest,
	sendTelegramTest,
	type TelegramSettingsInput,
	updateEmailSettings,
	updateTelegramSettings,
} from '@/modules/notifications/api/notification-settings.api';
import { NOTIFICATION_SETTINGS_QUERY_KEY } from '@/modules/notifications/hooks/use-notification-settings-queries';

/** El PUT devuelve la configuración completa: se guarda sin otro GET. */
function useStoreSettings() {
	const queryClient = useQueryClient();
	return (settings: NotificationSettings) =>
		queryClient.setQueryData(NOTIFICATION_SETTINGS_QUERY_KEY, settings);
}

function useUpdateTelegramSettingsMutation() {
	const store = useStoreSettings();
	return useMutation({
		mutationFn: (input: TelegramSettingsInput) => updateTelegramSettings(input),
		onSuccess: store,
	});
}

function useUpdateEmailSettingsMutation() {
	const store = useStoreSettings();
	return useMutation({
		mutationFn: (enabled: boolean) => updateEmailSettings(enabled),
		onSuccess: store,
	});
}

function useSendTelegramTestMutation() {
	return useMutation({ mutationFn: sendTelegramTest });
}

function useSendEmailTestMutation() {
	return useMutation({ mutationFn: sendEmailTest });
}

export {
	useSendEmailTestMutation,
	useSendTelegramTestMutation,
	useUpdateEmailSettingsMutation,
	useUpdateTelegramSettingsMutation,
};
