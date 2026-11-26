import type {
	AlertChannels,
	AlertDeliveryStatus,
	AlertRuleType,
	AlertSeverity,
} from '@/modules/alerts/api/alerts.api';
import {
	DELIVERY_LABELS,
	DELIVERY_VARIANTS,
	describeChannels,
	RULE_TYPE_LABELS,
	RULE_TYPE_VARIANTS,
	SEVERITY_LABELS,
	SEVERITY_VARIANTS,
} from '@/modules/alerts/lib/alerts-labels';
import { Badge } from '@/modules/ui/components/badge';

export function RuleTypeBadge({ type }: { type: AlertRuleType }) {
	return (
		<Badge variant={RULE_TYPE_VARIANTS[type] ?? 'outline'}>
			{RULE_TYPE_LABELS[type] ?? type}
		</Badge>
	);
}

export function RuleStatusBadge({ isActive }: { isActive: boolean }) {
	return (
		<Badge variant={isActive ? 'secondary' : 'outline'}>
			{isActive ? 'Activa' : 'Inactiva'}
		</Badge>
	);
}

export function SeverityBadge({ severity }: { severity: AlertSeverity }) {
	return (
		<Badge variant={SEVERITY_VARIANTS[severity] ?? 'outline'}>
			{SEVERITY_LABELS[severity] ?? severity}
		</Badge>
	);
}

export function DeliveryBadge({ status }: { status: AlertDeliveryStatus }) {
	return (
		<Badge variant={DELIVERY_VARIANTS[status] ?? 'outline'}>
			{DELIVERY_LABELS[status] ?? status}
		</Badge>
	);
}

export function ChannelsList({ channels }: { channels: AlertChannels }) {
	const names = describeChannels(channels);
	if (names.length === 0) {
		return <span className="text-muted-foreground">Ninguno</span>;
	}
	return (
		<div className="flex flex-wrap gap-1">
			{names.map((name) => (
				<Badge key={name} variant="outline">
					{name}
				</Badge>
			))}
		</div>
	);
}
