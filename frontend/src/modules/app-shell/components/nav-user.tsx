import { IconLogout, IconSelector } from '@tabler/icons-react';
import { useNavigate } from '@tanstack/react-router';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import { useLogoutMutation } from '@/modules/auth/hooks/use-auth-mutations';
import { Avatar, AvatarFallback } from '@/modules/ui/components/avatar';
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuGroup,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from '@/modules/ui/components/dropdown-menu';
import {
	SidebarMenu,
	SidebarMenuButton,
	SidebarMenuItem,
	useSidebar,
} from '@/modules/ui/components/sidebar';

/** Iniciales del nombre completo, o de la parte local del correo si no hay nombre. */
function getInitials(fullName: string | null, email: string) {
	const source = fullName?.trim() || email.split('@')[0];
	const words = source.split(/\s+/).filter(Boolean);
	const initials =
		words.length > 1 ? `${words[0][0]}${words[1][0]}` : source.slice(0, 2);
	return initials.toUpperCase();
}

function UserSummary({
	displayName,
	subtitle,
	initials,
}: {
	displayName: string;
	subtitle: string;
	initials: string;
}) {
	return (
		<>
			<Avatar className="h-8 w-8 rounded-lg">
				<AvatarFallback className="rounded-lg">{initials}</AvatarFallback>
			</Avatar>
			<div className="grid flex-1 text-left text-sm leading-tight">
				<span className="truncate font-medium">{displayName}</span>
				<span className="truncate text-xs">{subtitle}</span>
			</div>
		</>
	);
}

export function NavUser() {
	const { isMobile } = useSidebar();
	const navigate = useNavigate();
	const { user } = useAuth();
	const logoutMutation = useLogoutMutation();

	if (!user) return null;

	function handleLogout() {
		logoutMutation.mutate(undefined, {
			onSettled: () => navigate({ to: '/login' }),
		});
	}

	const displayName = user.full_name?.trim() || user.email.split('@')[0];
	const subtitle = user.role_label ?? user.email;
	const initials = getInitials(user.full_name, user.email);

	return (
		<SidebarMenu>
			<SidebarMenuItem>
				<DropdownMenu>
					<DropdownMenuTrigger
						render={
							<SidebarMenuButton
								size="lg"
								className="data-popup-open:bg-sidebar-accent data-popup-open:text-sidebar-accent-foreground"
							/>
						}
					>
						<UserSummary
							displayName={displayName}
							subtitle={subtitle}
							initials={initials}
						/>
						<IconSelector className="ml-auto size-4" />
					</DropdownMenuTrigger>
					<DropdownMenuContent
						className="w-(--anchor-width) min-w-56 rounded-lg"
						side={isMobile ? 'bottom' : 'right'}
						align="end"
						sideOffset={4}
					>
						<DropdownMenuGroup>
							<DropdownMenuLabel className="p-0 font-normal">
								<div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
									<UserSummary
										displayName={displayName}
										subtitle={user.email}
										initials={initials}
									/>
								</div>
							</DropdownMenuLabel>
						</DropdownMenuGroup>
						<DropdownMenuSeparator />
						<DropdownMenuItem onClick={handleLogout}>
							<IconLogout />
							Cerrar sesión
						</DropdownMenuItem>
					</DropdownMenuContent>
				</DropdownMenu>
			</SidebarMenuItem>
		</SidebarMenu>
	);
}
