import { IconChartCandle } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import {
	SidebarMenu,
	SidebarMenuButton,
	SidebarMenuItem,
} from '@/modules/ui/components/sidebar';

/** Marca de la app en la cabecera del sidebar: nombre + rol del usuario. */
export function AppBrand() {
	const { user } = useAuth();

	return (
		<SidebarMenu>
			<SidebarMenuItem>
				<SidebarMenuButton size="lg" render={<Link to="/dashboard" />}>
					<div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
						<IconChartCandle className="size-5" />
					</div>
					<div className="grid flex-1 text-left text-sm leading-tight">
						<span className="truncate font-semibold">Trading App</span>
						<span className="truncate text-xs text-muted-foreground">
							{user?.role_label ?? 'Trading asistido por IA'}
						</span>
					</div>
				</SidebarMenuButton>
			</SidebarMenuItem>
		</SidebarMenu>
	);
}
