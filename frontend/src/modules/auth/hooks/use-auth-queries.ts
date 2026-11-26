import { useQuery } from '@tanstack/react-query';
import { me } from '@/modules/auth/api/auth.api';

const TELEGRAM_LINK_STATUS_QUERY_KEY = [
	'auth',
	'telegram-link-status',
] as const;

// El backend procesa el "/start" del bot en el ciclo del scheduler (modo
// polling) o al recibir el webhook: el vínculo aparece unos segundos (hasta
// ~1 min) después de pulsar Iniciar. Mientras el enlace está abierto se relee
// `/users/me` en segundo plano. No usa `refreshUser()` porque ese marca la
// sesión como cerrada ante cualquier error de la API.
const TELEGRAM_LINK_POLL_MS = 4000;

function useTelegramLinkStatusQuery(enabled: boolean) {
	return useQuery({
		queryKey: TELEGRAM_LINK_STATUS_QUERY_KEY,
		queryFn: me,
		enabled,
		refetchInterval: enabled ? TELEGRAM_LINK_POLL_MS : false,
		gcTime: 0,
		select: (user) => user.telegram_linked,
	});
}

export { TELEGRAM_LINK_STATUS_QUERY_KEY, useTelegramLinkStatusQuery };
