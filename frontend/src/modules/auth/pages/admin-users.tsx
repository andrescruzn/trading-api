import {
	IconBan,
	IconDots,
	IconUserCheck,
	IconUserCog,
	IconUserOff,
	IconUserPlus,
} from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { UserSummary } from '@/modules/auth/api/users.api';
import { InviteUserDialog } from '@/modules/auth/components/invite-user-dialog';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import { UserRoleDialog } from '@/modules/auth/components/user-role-dialog';
import { UserStatusDialog } from '@/modules/auth/components/user-status-dialog';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import {
	useOwners,
	userDisplayName,
} from '@/modules/auth/hooks/use-users-queries';
import { ROLE_OPTIONS, ROLES } from '@/modules/auth/lib/roles';
import {
	USER_STATUS_ACTION_LABELS,
	USER_STATUSES,
	type UserStatus,
	type UserStatusChange,
	userStatusLabel,
} from '@/modules/auth/lib/user-status';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { formatDateTime } from '@/modules/shared/lib/format';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from '@/modules/ui/components/dropdown-menu';

const ALL = 'all';

const STATUS_ACTION_ICONS: Record<UserStatus, typeof IconBan> = {
	active: IconUserCheck,
	blocked: IconBan,
	disabled: IconUserOff,
};

const STATUS_ACTIONS: UserStatus[] = [
	USER_STATUSES.ACTIVE,
	USER_STATUSES.BLOCKED,
	USER_STATUSES.DISABLED,
];

/** Los propietarios no se tocan desde la app (ni rol ni estado). */
function isSuperAdmin(user: UserSummary) {
	return user.role_code === ROLES.SUPER_ADMIN;
}

const ROLE_FILTER_OPTIONS = [
	{ value: ALL, label: 'Todos los roles' },
	...ROLE_OPTIONS,
];

export function AdminUsersPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Usuarios' }]);
	const { user: currentUser } = useAuth();
	const canManage = useCanManage();
	const owners = useOwners(ALL);
	const [role, setRole] = useState(ALL);
	const [editing, setEditing] = useState<UserSummary | null>(null);
	const [statusChange, setStatusChange] = useState<UserStatusChange | null>(
		null,
	);
	const [inviting, setInviting] = useState(false);

	const allUsers = owners.usersQuery.data ?? [];
	const users = allUsers.filter(
		(user) => role === ALL || user.role_code === role,
	);

	const baseColumns: DataTableColumn<UserSummary>[] = [
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
					variant={
						row.role_code === ROLES.SUPER_ADMIN ? 'default' : 'secondary'
					}
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
					{userStatusLabel(row.status)}
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
	];

	// Solo un super admin cambia roles y estados; el socio ve la lista.
	const actionsColumn: DataTableColumn<UserSummary> = {
		id: 'actions',
		header: <span className="sr-only">Acciones</span>,
		className: 'text-right',
		cell: (row) =>
			row.id === currentUser?.id ? (
				// El backend no deja cambiar el propio rol ni el propio estado:
				// así nadie se deja fuera por error.
				<span className="text-sm text-muted-foreground">Tú</span>
			) : isSuperAdmin(row) ? null : (
				<DropdownMenu>
					<DropdownMenuTrigger
						render={<Button variant="ghost" size="icon-sm" />}
					>
						<IconDots />
						<span className="sr-only">Acciones de {userDisplayName(row)}</span>
					</DropdownMenuTrigger>
					<DropdownMenuContent align="end" className="w-auto min-w-44">
						<DropdownMenuItem onClick={() => setEditing(row)}>
							<IconUserCog />
							Cambiar rol
						</DropdownMenuItem>
						<DropdownMenuSeparator />
						{STATUS_ACTIONS.filter((status) => status !== row.status).map(
							(status) => {
								const Icon = STATUS_ACTION_ICONS[status];
								return (
									<DropdownMenuItem
										key={status}
										variant={
											status === USER_STATUSES.ACTIVE
												? 'default'
												: 'destructive'
										}
										onClick={() => setStatusChange({ user: row, status })}
									>
										<Icon />
										{USER_STATUS_ACTION_LABELS[status]}
									</DropdownMenuItem>
								);
							},
						)}
					</DropdownMenuContent>
				</DropdownMenu>
			),
	};

	const columns = canManage ? [...baseColumns, actionsColumn] : baseColumns;

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Usuarios"
				description="Quién tiene cuenta, con qué rol y si puede entrar. El rol decide qué ve cada persona en el menú; bloquear o desactivar una cuenta cierra su sesión."
				actions={[
					{
						label: 'Invitar usuario',
						icon: <IconUserPlus />,
						onClick: () => setInviting(true),
						hidden: !canManage,
					},
				]}
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
						: 'Aún no hay usuarios. Invita al primero.'
				}
			/>
			<InviteUserDialog open={inviting} onOpenChange={setInviting} />
			<UserRoleDialog
				user={editing}
				onOpenChange={(open) => !open && setEditing(null)}
			/>
			<UserStatusDialog
				change={statusChange}
				onOpenChange={(open) => !open && setStatusChange(null)}
			/>
		</div>
	);
}
