import {
	IconBell,
	IconBellCog,
	IconBook,
	IconCoins,
	IconCompass,
	IconDatabase,
	IconFlask,
	IconHome,
	IconSettings,
	IconTestPipe,
	IconTrophy,
} from '@tabler/icons-react';
import { useRouterState } from '@tanstack/react-router';
import type * as React from 'react';
import { useEffect, useState } from 'react';
import { AppBrand } from '@/modules/app-shell/components/app-brand';
import { NavSection } from '@/modules/app-shell/components/nav-section';
import type { NavSectionData } from '@/modules/app-shell/components/nav-section.types';
import {
	getDeclaredNavUrl,
	isPathActive,
} from '@/modules/app-shell/components/nav-section.utils';
import { NavUser } from '@/modules/app-shell/components/nav-user';
import { useBreadcrumbContext } from '@/modules/app-shell/hooks/use-breadcrumb-context';
import { STAFF_ROLES } from '@/modules/auth/lib/roles';
import {
	Sidebar,
	SidebarContent,
	SidebarFooter,
	SidebarHeader,
	SidebarRail,
} from '@/modules/ui/components/sidebar';

// Las secciones sin `role` las ve cualquier usuario autenticado (el inversor
// también: además ve "Mi inversión"). "Administración" la ven el super admin y
// el socio (este en solo lectura: las páginas ocultan las acciones).
// Orden: lo que se opera a diario arriba (agentes); lo de consulta, al final.
const navSections: NavSectionData[] = [
	{
		label: 'General',
		// El inicio es la lista de agentes reales (billetera de Binance). Los de
		// dinero simulado van aparte y conviven con los reales. Reales y demo
		// comparten `/agents/:id`: el ítem marcado lo decide la raíz de la miga
		// (`getDeclaredNavUrl`); `activePaths` solo cubre la carga inicial.
		items: [
			{
				title: 'Inicio',
				icon: IconHome,
				url: '/dashboard',
				activePaths: ['/agents'],
			},
			{
				title: 'Agentes demo',
				icon: IconTestPipe,
				url: '/demo-agents',
				role: STAFF_ROLES,
			},
		],
	},
	{
		label: 'Operar',
		items: [{ title: 'Alertas', icon: IconBell, url: '/alerts' }],
	},
	{
		label: 'Explorar',
		items: [
			{
				title: 'Explorar mercados',
				icon: IconCompass,
				url: '/market/explorer',
			},
			{ title: 'Estrategias', icon: IconBook, url: '/strategies' },
			{ title: 'Track record', icon: IconTrophy, url: '/track-record' },
			{ title: 'Backtesting', icon: IconFlask, url: '/backtest' },
		],
	},
	{
		// Todos son participantes del fondo común: propietarios, socios e
		// inversores tienen su saldo.
		label: 'Mi inversión',
		items: [{ title: 'Mi saldo', icon: IconCoins, url: '/my-fund' }],
	},
	{
		label: 'Administración',
		role: STAFF_ROLES,
		items: [
			{
				// Telegram y correo: por dónde llegan los avisos (el socio lo ve
				// en solo lectura).
				title: 'Notificaciones',
				icon: IconBellCog,
				url: '/admin/notifications',
			},
			{
				// El fondo común: resumen y conciliación, el saldo de la billetera
				// de Binance (la única: nadie la elige), depósitos, retiros y
				// comisiones. El socio lo ve en solo lectura.
				title: 'Fondo',
				icon: IconCoins,
				items: [
					{ title: 'Resumen del fondo', url: '/admin/fund' },
					{ title: 'Billetera', url: '/admin/wallet' },
					{ title: 'Depósitos', url: '/admin/deposits' },
					{ title: 'Retiros', url: '/admin/withdrawals' },
					{ title: 'Agentes del fondo', url: '/admin/fund-agents' },
					{ title: 'Comisiones', url: '/admin/commissions' },
					{ title: 'Participantes', url: '/admin/participants' },
					{ title: 'Ajustes del fondo', url: '/admin/fund-settings' },
				],
			},
			{
				title: 'Datos de mercado',
				icon: IconDatabase,
				items: [
					{ title: 'Símbolos', url: '/admin/symbols' },
					{ title: 'Timeframes', url: '/admin/timeframes' },
					{ title: 'Conjuntos de indicadores', url: '/admin/feature-sets' },
				],
			},
			{
				// Lo que el super admin define para todo el sistema.
				title: 'Configuración',
				icon: IconSettings,
				items: [
					{ title: 'Usuarios', url: '/admin/users' },
					{ title: 'Auditoría', url: '/admin/audit' },
				],
			},
		],
	},
];

function getActiveParentTitle(pathname: string, declaredUrl: string | null) {
	for (const section of navSections) {
		for (const item of section.items) {
			const hasActiveSubItem = item.items?.some((subItem) =>
				declaredUrl
					? subItem.url === declaredUrl
					: isPathActive(pathname, subItem.url),
			);
			if (hasActiveSubItem) return item.title;
		}
	}
	return null;
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
	const pathname = useRouterState({
		select: (state) => state.location.pathname,
	});
	const { items: breadcrumbItems } = useBreadcrumbContext();
	const declaredUrl = getDeclaredNavUrl(
		navSections,
		pathname,
		breadcrumbItems[0]?.href,
	);
	const activeParentTitle = getActiveParentTitle(pathname, declaredUrl);
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
						declaredUrl={declaredUrl}
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
