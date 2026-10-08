import { IconLock, IconLockOpen } from '@tabler/icons-react';
import type { Account } from '@/modules/accounts/api/accounts.api';
import {
	ACCOUNT_MODE_BADGE_VARIANT,
	ACCOUNT_MODE_LABELS,
	ACCOUNT_STATUS_BADGE_VARIANT,
	ACCOUNT_STATUS_LABELS,
} from '@/modules/accounts/lib/accounts-labels';
import { Badge } from '@/modules/ui/components/badge';

export function AccountModeBadge({ mode }: { mode: Account['mode'] }) {
	return (
		<Badge variant={ACCOUNT_MODE_BADGE_VARIANT[mode] ?? 'outline'}>
			{ACCOUNT_MODE_LABELS[mode] ?? mode}
		</Badge>
	);
}

export function AccountStatusBadge({ status }: { status: Account['status'] }) {
	return (
		<Badge variant={ACCOUNT_STATUS_BADGE_VARIANT[status] ?? 'outline'}>
			{ACCOUNT_STATUS_LABELS[status] ?? status}
		</Badge>
	);
}

/** Solo indica si hay credenciales guardadas: el valor nunca llega al navegador. */
export function CredentialsIndicator({ account }: { account: Account }) {
	const label = account.has_credentials
		? 'Credenciales cifradas guardadas'
		: 'Sin credenciales';

	return (
		<span className="inline-flex items-center gap-1.5" title={label}>
			{account.has_credentials ? (
				<IconLock className="size-4 text-chart-1" aria-hidden="true" />
			) : (
				<IconLockOpen className="size-4 text-muted-foreground" aria-hidden="true" />
			)}
			<span className="sr-only">{label}</span>
		</span>
	);
}
