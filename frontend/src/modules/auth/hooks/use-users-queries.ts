import { useQuery } from '@tanstack/react-query';
import { listUsers, type UserSummary } from '@/modules/auth/api/users.api';
import type { SelectOption } from '@/modules/shared/components/option-select';

const USERS_QUERY_KEY = ['users'] as const;

// Catálogo que cambia poco: se reutiliza entre las vistas de Administración.
const USERS_STALE_TIME = 5 * 60 * 1000;

/** Solo admin: el backend responde 403 a cualquier otro rol. */
function useUsersQuery() {
	return useQuery({
		queryKey: USERS_QUERY_KEY,
		queryFn: listUsers,
		staleTime: USERS_STALE_TIME,
	});
}

function userDisplayName(user: UserSummary) {
	return user.full_name?.trim() || user.email;
}

/**
 * Usuarios como `id → usuario` (para la columna Dueño) y como opciones del
 * filtro, con "Todos los usuarios" primero y el resto por nombre.
 */
function useOwners(allValue: string) {
	const usersQuery = useUsersQuery();
	const users = usersQuery.data ?? [];

	const byId = new Map<number, UserSummary>();
	for (const user of users) byId.set(user.id, user);

	const options: SelectOption[] = [
		{ value: allValue, label: 'Todos los usuarios' },
		...users
			.map((user) => ({ value: String(user.id), label: userDisplayName(user) }))
			.sort((a, b) => a.label.localeCompare(b.label, 'es')),
	];

	return { usersQuery, byId, options };
}

export { USERS_QUERY_KEY, useOwners, userDisplayName, useUsersQuery };
