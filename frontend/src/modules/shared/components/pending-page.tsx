import { IconLoader2 } from '@tabler/icons-react';

export function PendingPage() {
	return (
		<div className="flex min-h-svh flex-col items-center justify-center gap-4 p-6 text-center">
			<IconLoader2 className="size-8 animate-spin text-muted-foreground" />
		</div>
	);
}
