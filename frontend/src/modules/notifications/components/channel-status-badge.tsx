import { Badge } from '@/modules/ui/components/badge';

type ChannelStatusBadgeProps = {
	active: boolean;
	/** Tiene lo necesario para funcionar (token, SMTP…). */
	configured: boolean;
};

/** Estado de un canal: Activo · Apagado · Sin configurar. */
export function ChannelStatusBadge({
	active,
	configured,
}: ChannelStatusBadgeProps) {
	if (active) return <Badge>Activo</Badge>;
	if (!configured) return <Badge variant="outline">Sin configurar</Badge>;
	return <Badge variant="secondary">Apagado</Badge>;
}
