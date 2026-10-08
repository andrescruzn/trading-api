import { IconChevronRight } from '@tabler/icons-react';
import { Link, useRouterState } from '@tanstack/react-router';
import type { CurrentUser } from '@/modules/auth/api/auth.api';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import { hasAnyRole } from '@/modules/auth/lib/roles';
import {
	Collapsible,
	CollapsibleContent,
	CollapsibleTrigger,
} from '@/modules/ui/components/collapsible';
import {
	SidebarGroup,
	SidebarGroupLabel,
	SidebarMenu,
	SidebarMenuButton,
	SidebarMenuItem,
	SidebarMenuSub,
	SidebarMenuSubButton,
	SidebarMenuSubItem,
	useSidebar,
} from '@/modules/ui/components/sidebar';
import type { NavItem, NavRole, NavSectionData } from './nav-section.types';
import { isPathActive } from './nav-section.utils';

function isVisible(user: CurrentUser | null, role?: NavRole) {
	if (!role) return true;
	if (!user) return false;
	return hasAnyRole(user, typeof role === 'string' ? [role] : role);
}

function getVisibleItems(user: CurrentUser | null, items: NavItem[]) {
	return items
		.map((item) => {
			if (!item.items) {
				return isVisible(user, item.role) ? item : null;
			}

			const visibleSubItems = item.items.filter((subItem) =>
				isVisible(user, subItem.role),
			);

			return visibleSubItems.length > 0
				? { ...item, items: visibleSubItems }
				: null;
		})
		.filter((item): item is NavItem => item !== null);
}

type NavSectionProps = NavSectionData & {
	openItem: string | null;
	onOpenItemChange: (title: string | null) => void;
};

export function NavSection({
	label,
	role,
	items,
	openItem,
	onOpenItemChange,
}: NavSectionProps) {
	const { user } = useAuth();
	const { setOpenMobile } = useSidebar();
	const pathname = useRouterState({
		select: (state) => state.location.pathname,
	});
	const visibleItems = isVisible(user, role)
		? getVisibleItems(user, items)
		: [];

	if (visibleItems.length === 0) return null;

	return (
		<SidebarGroup>
			<SidebarGroupLabel>{label}</SidebarGroupLabel>
			<SidebarMenu>
				{visibleItems.map((item) =>
					item.items ? (
						<Collapsible
							key={item.title}
							className="group/collapsible"
							open={openItem === item.title}
							onOpenChange={(open) =>
								onOpenItemChange(open ? item.title : null)
							}
							render={<SidebarMenuItem />}
						>
							<CollapsibleTrigger
								render={
									<SidebarMenuButton
										tooltip={item.title}
										isActive={item.items.some((subItem) =>
											isPathActive(pathname, subItem.url),
										)}
									/>
								}
							>
								{item.icon && <item.icon />}
								<span>{item.title}</span>
								<IconChevronRight className="ml-auto transition-transform duration-200 group-data-open/collapsible:rotate-90" />
							</CollapsibleTrigger>
							<CollapsibleContent>
								<SidebarMenuSub>
									{item.items.map((subItem) => (
										<SidebarMenuSubItem key={subItem.title}>
											<SidebarMenuSubButton
												isActive={isPathActive(pathname, subItem.url)}
												render={
													<Link
														to={subItem.url}
														onClick={() => setOpenMobile(false)}
													/>
												}
											>
												<span>{subItem.title}</span>
											</SidebarMenuSubButton>
										</SidebarMenuSubItem>
									))}
								</SidebarMenuSub>
							</CollapsibleContent>
						</Collapsible>
					) : (
						<SidebarMenuItem key={item.title}>
							<SidebarMenuButton
								tooltip={item.title}
								isActive={
									isPathActive(pathname, item.url) ||
									!!item.activePaths?.some((path) =>
										isPathActive(pathname, path),
									)
								}
								render={
									<Link
										to={item.url ?? '#'}
										onClick={() => setOpenMobile(false)}
									/>
								}
							>
								{item.icon && <item.icon />}
								<span>{item.title}</span>
							</SidebarMenuButton>
						</SidebarMenuItem>
					),
				)}
			</SidebarMenu>
		</SidebarGroup>
	);
}
