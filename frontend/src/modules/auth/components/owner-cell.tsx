import type { UserSummary } from '@/modules/auth/api/users.api';

type OwnerCellProps = {
	userId: number | null | undefined;
	users: Map<number, UserSummary>;
};

/** Dueño en una tabla: nombre y, debajo, el correo (sin nombre, solo el correo). */
export function OwnerCell({ userId, users }: OwnerCellProps) {
	if (userId == null) {
		return <span className="text-muted-foreground">—</span>;
	}
	const user = users.get(userId);
	if (!user) {
		return (
			<span className="font-mono text-muted-foreground">Usuario #{userId}</span>
		);
	}
	const name = user.full_name?.trim();
	if (!name) return <span>{user.email}</span>;
	return (
		<div className="flex flex-col">
			<span className="font-medium">{name}</span>
			<span className="text-xs text-muted-foreground">{user.email}</span>
		</div>
	);
}
