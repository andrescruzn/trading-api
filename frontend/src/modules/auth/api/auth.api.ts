import type { RoleCode } from '@/modules/auth/lib/roles';
import { api } from '@/modules/shared/lib/api-client';

/** `GET /users/me` — perfil del usuario autenticado. */
type CurrentUser = {
	id: number;
	email: string;
	full_name: string | null;
	role_id: number;
	role_code: RoleCode | null;
	role_label: string | null;
	status: string;
	last_login_at: string | null;
	created_at: string | null;
};

/** Login exitoso: la sesión viaja en la cookie HttpOnly, no en el body. */
type LoginResult = {
	authenticated: boolean;
	expires_at: string;
};

/** `POST /users/login` sin contraseña: se envió un código por correo. */
type OtpRequestResult = {
	otp_required: boolean;
	email: string;
	otp_expires_at: string;
	/** Solo llega con `APP_ENV=development`. */
	otp_code?: string;
};

function login(email: string, password: string) {
	return api.post<LoginResult>('/users/login', { email, password });
}

function requestOtp(email: string) {
	return api.post<OtpRequestResult>('/users/login', { email });
}

function verifyOtp(email: string, otpCode: string) {
	return api.post<LoginResult>('/users/login/otp/verify', {
		email,
		otp_code: otpCode,
	});
}

function logout() {
	return api.post<null>('/users/logout');
}

function me() {
	return api.get<CurrentUser>('/users/me');
}

/** Cambia la contraseña. El backend revoca la sesión y borra la cookie. */
function changePassword(currentPassword: string, newPassword: string) {
	return api.patch<null>('/users/me/password', {
		current_password: currentPassword,
		new_password: newPassword,
	});
}

export type { CurrentUser, LoginResult, OtpRequestResult };
export { changePassword, login, logout, me, requestOtp, verifyOtp };
