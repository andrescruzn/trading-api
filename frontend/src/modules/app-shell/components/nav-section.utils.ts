import type { NavSectionData } from './nav-section.types';

export function isPathActive(pathname: string, url?: string) {
	if (!url) return false;
	return pathname === url || pathname.startsWith(`${url}/`);
}

/** URLs de todos los ítems y subítems del menú. */
function getNavUrls(sections: NavSectionData[]) {
	return sections.flatMap((section) =>
		section.items.flatMap((item) => [
			...(item.url ? [item.url] : []),
			...(item.items?.map((subItem) => subItem.url) ?? []),
		]),
	);
}

/**
 * Sección que la página declara como raíz de su miga, cuando la URL no
 * corresponde a ningún ítem del menú. Así el sidebar y la miga coinciden en
 * pantallas que comparten URL pero cuelgan de secciones distintas (el detalle
 * de un agente real cuelga de Inicio; el de uno demo, de Agentes demo).
 */
function getDeclaredNavUrl(
	sections: NavSectionData[],
	pathname: string,
	breadcrumbRootHref?: string,
) {
	if (!breadcrumbRootHref) return null;
	const urls = getNavUrls(sections);
	if (urls.some((url) => isPathActive(pathname, url))) return null;
	return urls.includes(breadcrumbRootHref) ? breadcrumbRootHref : null;
}

export { getDeclaredNavUrl };
