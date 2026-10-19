import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	createTelegramLink,
	logout,
	requestOtp,
	unlinkTelegram,
	verifyOtp,
} from '@/modules/auth/api/auth.api';
import { useAuth } from '@/modules/auth/hooks/use-auth';

function useRequestOtpMutation() {
	return useMutation({
		mutationFn: (email: string) => requestOtp(email),
	});
}

// Verificar el código no devuelve el usuario (solo pone la cookie): tras
// autenticarse se pide `GET /users/me` para cargar el perfil y el rol.
function useVerifyOtpMutation() {
	const { refreshUser } = useAuth();
	return useMutation({
		mutationFn: ({ email, code }: { email: string; code: string }) =>
			verifyOtp(email, code),
		onSuccess: () => refreshUser(),
	});
}

function useLogoutMutation() {
	const { clear } = useAuth();
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: logout,
		onSettled: () => {
			queryClient.clear();
			clear();
		},
	});
}

function useCreateTelegramLinkMutation() {
	return useMutation({ mutationFn: createTelegramLink });
}

/** Tras desvincular se recarga el perfil (`telegram_linked`). */
function useUnlinkTelegramMutation() {
	const { refreshUser } = useAuth();
	return useMutation({
		mutationFn: unlinkTelegram,
		onSuccess: () => refreshUser(),
	});
}

export {
	useCreateTelegramLinkMutation,
	useLogoutMutation,
	useRequestOtpMutation,
	useUnlinkTelegramMutation,
	useVerifyOtpMutation,
};
