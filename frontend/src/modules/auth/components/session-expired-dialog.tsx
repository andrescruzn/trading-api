import { IconClockX } from '@tabler/icons-react';
import { useSessionExpiredStore } from '@/modules/auth/lib/session-expired-store';
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogMedia,
	AlertDialogTitle,
} from '@/modules/ui/components/alert-dialog';

function SessionExpiredDialog() {
	const visible = useSessionExpiredStore((state) => state.visible);
	const acknowledgeSessionExpired = useSessionExpiredStore(
		(state) => state.acknowledgeSessionExpired,
	);

	return (
		<AlertDialog
			open={visible}
			onOpenChange={(open) => {
				if (!open) acknowledgeSessionExpired();
			}}
		>
			<AlertDialogContent size="sm">
				<AlertDialogHeader>
					<AlertDialogMedia>
						<IconClockX />
					</AlertDialogMedia>
					<AlertDialogTitle>Tu sesión expiró</AlertDialogTitle>
					<AlertDialogDescription>
						Por seguridad la cerramos. Ingresa de nuevo para seguir.
					</AlertDialogDescription>
				</AlertDialogHeader>
				<AlertDialogFooter className="sm:justify-center">
					<AlertDialogAction
						onClick={acknowledgeSessionExpired}
						className="flex-1"
					>
						Ingresar de nuevo
					</AlertDialogAction>
				</AlertDialogFooter>
			</AlertDialogContent>
		</AlertDialog>
	);
}

export { SessionExpiredDialog };
