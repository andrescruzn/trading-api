import { IconHome } from '@tabler/icons-react';
import { Link, Navigate, Outlet } from '@tanstack/react-router';
import { Fragment } from 'react';
import { AppSidebar } from '@/modules/app-shell/components/app-sidebar';
import { useBreadcrumbContext } from '@/modules/app-shell/hooks/use-breadcrumb-context';
import { BreadcrumbProvider } from '@/modules/app-shell/lib/breadcrumb-provider';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import {
	Breadcrumb,
	BreadcrumbItem,
	BreadcrumbLink,
	BreadcrumbList,
	BreadcrumbPage,
	BreadcrumbSeparator,
} from '@/modules/ui/components/breadcrumb';
import { Separator } from '@/modules/ui/components/separator';
import {
	SidebarInset,
	SidebarProvider,
	SidebarTrigger,
} from '@/modules/ui/components/sidebar';

function AppBreadcrumb() {
	const { items } = useBreadcrumbContext();

	return (
		<Breadcrumb>
			<BreadcrumbList>
				<BreadcrumbItem>
					<BreadcrumbLink render={<Link to="/dashboard" />}>
						<IconHome className="size-4" />
						<span className="sr-only">Inicio</span>
					</BreadcrumbLink>
				</BreadcrumbItem>
				{items.length > 0 && <BreadcrumbSeparator />}
				{items.map((item, index) => {
					const isLast = index === items.length - 1;
					return (
						<Fragment key={item.label}>
							<BreadcrumbItem>
								{isLast || !item.href ? (
									<BreadcrumbPage>{item.label}</BreadcrumbPage>
								) : (
									<BreadcrumbLink render={<Link to={item.href} />}>
										{item.label}
									</BreadcrumbLink>
								)}
							</BreadcrumbItem>
							{!isLast && <BreadcrumbSeparator />}
						</Fragment>
					);
				})}
			</BreadcrumbList>
		</Breadcrumb>
	);
}

/**
 * Shell de la app autenticada (todos los roles): sidebar + cabecera con
 * breadcrumb + contenido. Sin sesión, redirige a `/login`.
 */
export function AppShellLayout() {
	const { status } = useAuth();

	if (status !== 'authenticated') {
		return <Navigate to="/login" />;
	}

	return (
		<BreadcrumbProvider>
			<SidebarProvider>
				<AppSidebar />
				<SidebarInset>
					<header className="flex shrink-0 items-center gap-x-2 gap-y-1 transition-[width,height] ease-linear min-h-16 sticky top-0 z-39 py-2 bg-background">
						<div className="flex items-center gap-2 px-4">
							<SidebarTrigger className="-ml-1" />
							<Separator
								orientation="vertical"
								className="mr-2 data-[orientation=vertical]:h-4 data-[orientation=vertical]:self-auto"
							/>
							<AppBreadcrumb />
						</div>
					</header>
					<div className="flex min-w-0 flex-1 flex-col gap-4 px-4 pt-0 pb-10">
						<Outlet />
					</div>
				</SidebarInset>
			</SidebarProvider>
		</BreadcrumbProvider>
	);
}
