import { IconLoader2 } from '@tabler/icons-react';
import type { Bot } from '@/modules/bots/api/bots.api';
import { describeBot } from '@/modules/bots/lib/bots-labels';
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from '@/modules/ui/components/alert-dialog';

type StopBotDialogProps = {
	bot: Pick<Bot, 'id' | 'name'>;
	open: boolean;
	onOpenChange: (open: boolean) => void;
	onConfirm: () => void;
	isPending: boolean;
};

/** Confirmación antes de detener un agente: deja de analizar el mercado. */
export function StopBotDialog({
	bot,
	open,
	onOpenChange,
	onConfirm,
	isPending,
}: StopBotDialogProps) {
	return (
		<AlertDialog open={open} onOpenChange={onOpenChange}>
			<AlertDialogContent>
				<AlertDialogHeader>
					<AlertDialogTitle>¿Detener «{describeBot(bot)}»?</AlertDialogTitle>
					<AlertDialogDescription>
						El agente deja de descargar velas y de generar señales. Las
						posiciones abiertas no se cierran.
					</AlertDialogDescription>
				</AlertDialogHeader>
				<AlertDialogFooter>
					<AlertDialogCancel>Cancelar</AlertDialogCancel>
					<AlertDialogAction
						variant="destructive"
						disabled={isPending}
						onClick={onConfirm}
					>
						{isPending && <IconLoader2 className="animate-spin" />}
						Detener agente
					</AlertDialogAction>
				</AlertDialogFooter>
			</AlertDialogContent>
		</AlertDialog>
	);
}
