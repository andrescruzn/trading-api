import {
	IconBell,
	IconBook,
	IconCoins,
	IconCompass,
	IconDatabase,
	IconEye,
	IconFlask,
	IconHome,
	IconSettings,
	IconTrophy,
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
import { MANAGER_ROLES, STAFF_ROLES } from '@/modules/auth/lib/roles';
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
		// El inicio es la lista de agentes: queda marcado también dentro de uno.
		items: [
			{
				title: 'Inicio',
				icon: IconHome,
				url: '/dashboard',
				activePaths: ['/agents'],
			},
		],
	},
	{
		label: 'Operar',
		items: [
			{ title: 'Alertas', icon: IconBell, url: '/alerts' },
			// Solo los super admin tienen cuentas de exchange (las operan ellos).
			{
				title: 'Mis cuentas',
				icon: IconWallet,
				url: '/portfolio',
				role: MANAGER_ROLES,
			},
		],
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
				// El fondo común: resumen y conciliación, la billetera única,
				// depósitos, retiros y comisiones. El socio lo ve en solo lectura.
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
					{ title: 'Exchanges', url: '/admin/exchanges' },
					{ title: 'Símbolos', url: '/admin/symbols' },
					{ title: 'Timeframes', url: '/admin/timeframes' },
					{ title: 'Conjuntos de indicadores', url: '/admin/feature-sets' },
				],
			},
			{
				// Lo de todos los usuarios (solo lectura): los nombres dicen el
				// alcance para no confundirse con los agentes del inicio o "Mis
				// cuentas" de Operar.
				title: 'Supervisión',
				icon: IconEye,
				items: [
					{ title: 'Todos los agentes', url: '/admin/agents' },
					{ title: 'Todas las cuentas', url: '/admin/accounts' },
					{ title: 'Todas las órdenes', url: '/admin/orders' },
					{ title: 'Todas las alertas', url: '/admin/alerts' },
				],
			},
			{
				// Lo que el super admin define para todo el sistema.
				title: 'Configuración',
				icon: IconSettings,
				items: [
					{ title: 'Usuarios', url: '/admin/users' },
					{ title: 'Telegram', url: '/admin/telegram', role: MANAGER_ROLES },
					{ title: 'Auditoría', url: '/admin/audit' },
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
