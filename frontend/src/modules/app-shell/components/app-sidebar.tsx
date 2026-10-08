import {
	IconBell,
	IconBook,
	IconBriefcase,
	IconChartCandle,
	IconChartLine,
	IconCpu,
	IconDatabase,
	IconHome,
	IconList,
	IconReceipt,
	IconRobot,
	IconTrendingUp,
	IconWallet,
} from '@tabler/icons-react';
import { useRouterState } from '@tanstack/react-router';
import type * as React from 'react';
import { useEffect, useState } from 'react';
import { AppBrand } from '@/modules/app-shell/components/app-brand';
import { NavSection } from '@/modules/app-shell/components/nav-section';
import type { NavSectionData } from '@/modules/app-shell/components/nav-section.types';
import { isPathActive } from '@/modules/app-shell/components/nav-section.utils';
import { NavUser } from '@/modules/app-shell/components/nav-user';
import { ROLES } from '@/modules/auth/lib/roles';
import {
	Sidebar,
	SidebarContent,
	SidebarFooter,
	SidebarHeader,
	SidebarRail,
} from '@/modules/ui/components/sidebar';

// Las secciones sin `role` las ve cualquier usuario autenticado (el inversor
// también: además ve "Mi inversión"). "Administración" solo la ve `admin`.
const navSections: NavSectionData[] = [
	{
		label: 'General',
		items: [{ title: 'Inicio', icon: IconHome, url: '/dashboard' }],
	},
	{
		label: 'Mercado',
		items: [
			{ title: 'Símbolos', icon: IconList, url: '/market/symbols' },
			{ title: 'Velas OHLCV', icon: IconChartCandle, url: '/market/candles' },
			{ title: 'Indicadores', icon: IconChartLine, url: '/features' },
		],
	},
	{
		label: 'Trading',
		items: [
			{ title: 'Mis cuentas', icon: IconWallet, url: '/portfolio' },
			{ title: 'Estrategias', icon: IconBook, url: '/strategies' },
			{ title: 'Agente de IA', icon: IconRobot, url: '/agent' },
			{ title: 'Bots', icon: IconCpu, url: '/bots' },
			{ title: 'Órdenes', icon: IconReceipt, url: '/orders' },
			{ title: 'Alertas', icon: IconBell, url: '/alerts' },
		],
	},
	{
		label: 'Mi inversión',
		role: ROLES.INVESTOR,
		items: [
			{
				title: 'Mi dashboard',
				icon: IconTrendingUp,
				url: '/investor/dashboard',
			},
		],
	},
	{
		label: 'Administración',
		role: ROLES.ADMIN,
		items: [
			{
				title: 'Datos de mercado',
				icon: IconDatabase,
				items: [
					{ title: 'Exchanges', url: '/admin/exchanges' },
					{ title: 'Símbolos', url: '/admin/symbols' },
					{ title: 'Timeframes', url: '/admin/timeframes' },
					{ title: 'Descargar velas', url: '/admin/candles/ingest' },
					{ title: 'Feature sets', url: '/admin/feature-sets' },
				],
			},
			{
				title: 'Operación',
				icon: IconCpu,
				items: [
					{ title: 'Cuentas', url: '/admin/accounts' },
					{ title: 'Estrategias', url: '/admin/strategies' },
					{ title: 'Bots', url: '/admin/bots' },
					{ title: 'Órdenes', url: '/admin/orders' },
					{ title: 'Alertas', url: '/admin/alerts' },
					{ title: 'Telegram', url: '/admin/telegram' },
				],
			},
			{
				title: 'Inversores',
				icon: IconBriefcase,
				items: [
					{ title: 'Inversores', url: '/admin/investors' },
					{ title: 'Cuentas gestionadas', url: '/admin/managed-accounts' },
					{ title: 'Facturación', url: '/admin/billing' },
				],
			},
		],
	},
];

function getActiveParentTitle(pathname: string) {
	for (const section of navSections) {
		for (const item of section.items) {
			if (item.items?.some((subItem) => isPathActive(pathname, subItem.url))) {
				return item.title;
			}
		}
	}
	return null;
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
	const pathname = useRouterState({
		select: (state) => state.location.pathname,
	});
	const activeParentTitle = getActiveParentTitle(pathname);
	const [openItem, setOpenItem] = useState<string | null>(activeParentTitle);

	// Al navegar, solo queda abierto el acordeón que contiene el link activo.
	useEffect(() => {
		setOpenItem(activeParentTitle);
	}, [activeParentTitle]);

	return (
		<Sidebar collapsible="icon" {...props}>
			<SidebarHeader>
				<AppBrand />
			</SidebarHeader>
			<SidebarContent>
				{navSections.map((section) => (
					<NavSection
						key={section.label}
						{...section}
						openItem={openItem}
						onOpenItemChange={setOpenItem}
					/>
				))}
			</SidebarContent>
			<SidebarFooter>
				<NavUser />
			</SidebarFooter>
			<SidebarRail />
		</Sidebar>
	);
}
