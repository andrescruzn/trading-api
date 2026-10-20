import { IconUserCog } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { UserSummary } from '@/modules/auth/api/users.api';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import { UserRoleDialog } from '@/modules/auth/components/user-role-dialog';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import { useOwners } from '@/modules/auth/hooks/use-users-queries';
import { ROLE_OPTIONS, ROLES } from '@/modules/auth/lib/roles';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDateTime } from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';

const ALL = 'all';

const STATUS_LABELS: Record<string, string> = {
	active: 'Activo',
	blocked: 'Bloqueado',
	disabled: 'Desactivado',
};

const ROLE_FILTER_OPTIONS = [
	{ value: ALL, label: 'Todos los roles' },
	...ROLE_OPTIONS,
];

export function AdminUsersPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Usuarios' }]);
	const { user: currentUser } = useAuth();
	const owners = useOwners(ALL);
	const [role, setRole] = useState(ALL);
	const [editing, setEditing] = useState<UserSummary | null>(null);

	const allUsers = owners.usersQuery.data ?? [];
	const users = allUsers.filter(
		(user) => role === ALL || user.role_code === role,
	);

	const columns: DataTableColumn<UserSummary>[] = [
		{
			id: 'user',
			header: 'Usuario',
			cell: (row) => <OwnerCell userId={row.id} users={owners.byId} />,
			skeletonClassName: 'w-40',
		},
		{
			id: 'role',
			header: 'Rol',
			cell: (row) => (
				<Badge
					variant={row.role_code === ROLES.ADMIN ? 'default' : 'secondary'}
				>
					{row.role_label ?? row.role_code ?? '—'}
				</Badge>
			),
		},
		{
			id: 'status',
			header: 'Estado',
			cell: (row) => (
				<Badge variant={row.status === 'active' ? 'outline' : 'destructive'}>
					{STATUS_LABELS[row.status] ?? row.status}
				</Badge>
			),
		},
		{
			id: 'last-login',
			header: 'Último ingreso',
			className: 'whitespace-nowrap',
			cell: (row) =>
				row.last_login_at ? (
					formatDateTime(row.last_login_at)
				) : (
					<span className="text-muted-foreground">Nunca</span>
				),
		},
		{
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) =>
				row.id === currentUser?.id ? (
					// El backend no deja cambiar el propio rol: así nunca falta un admin.
					<span className="text-sm text-muted-foreground">Tú</span>
				) : (
					<Button variant="ghost" size="sm" onClick={() => setEditing(row)}>
						<IconUserCog />
						Cambiar rol
					</Button>
				),
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Usuarios"
				description="Quién tiene cuenta y con qué rol. El rol decide qué ve cada persona en el menú y qué puede hacer."
			/>
			<div className="grid gap-3 sm:max-w-xs">
				<OptionSelect
					aria-label="Rol"
					size="sm"
					value={role}
					onChange={(value) => setRole(value ?? ALL)}
					options={ROLE_FILTER_OPTIONS}
				/>
			</div>
			<DataTable
				columns={columns}
				rows={owners.usersQuery.data ? users : undefined}
				getRowId={(row) => row.id}
				isLoading={owners.usersQuery.isLoading}
				error={owners.usersQuery.error}
				errorTitle="No pudimos cargar los usuarios"
				empty={
					allUsers.length > 0
						? 'No hay usuarios con ese rol.'
						: 'Aún no hay usuarios.'
				}
			/>
			<UserRoleDialog
				user={editing}
				onOpenChange={(open) => !open && setEditing(null)}
			/>
		</div>
	);
}
