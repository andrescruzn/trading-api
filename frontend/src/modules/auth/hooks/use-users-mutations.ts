import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
	type InviteUserInput,
	inviteUser,
	updateUserRole,
} from '@/modules/auth/api/users.api';
import { USERS_QUERY_KEY } from '@/modules/auth/hooks/use-users-queries';
import type { RoleCode } from '@/modules/auth/lib/roles';

function useUpdateUserRoleMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: ({ id, roleCode }: { id: number; roleCode: RoleCode }) =>
			updateUserRole(id, roleCode),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: USERS_QUERY_KEY }),
	});
}

function useInviteUserMutation() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (input: InviteUserInput) => inviteUser(input),
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: USERS_QUERY_KEY }),
	});
}

export { useInviteUserMutation, useUpdateUserRoleMutation };
