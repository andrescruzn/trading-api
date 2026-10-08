import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	changePassword,
	login,
	logout,
	requestOtp,
	verifyOtp,
} from '@/modules/auth/api/auth.api';
import { useAuth } from '@/modules/auth/hooks/use-auth';

// El login no devuelve el usuario (solo pone la cookie): tras autenticarse se
// pide `GET /users/me` para cargar el perfil y el rol.
function useLoginMutation() {
	const { refreshUser } = useAuth();
	return useMutation({
		mutationFn: ({ email, password }: { email: string; password: string }) =>
			login(email, password),
		onSuccess: () => refreshUser(),
	});
}

function useRequestOtpMutation() {
	return useMutation({
		mutationFn: (email: string) => requestOtp(email),
	});
}

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

// El backend revoca la sesión al cambiar la contraseña: hay que volver a entrar.
function useChangePasswordMutation() {
	const { clear } = useAuth();
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({
			currentPassword,
			newPassword,
		}: {
			currentPassword: string;
			newPassword: string;
		}) => changePassword(currentPassword, newPassword),
		onSuccess: () => {
			queryClient.clear();
			clear();
		},
	});
}

export {
	useChangePasswordMutation,
	useLoginMutation,
	useLogoutMutation,
	useRequestOtpMutation,
	useVerifyOtpMutation,
};
