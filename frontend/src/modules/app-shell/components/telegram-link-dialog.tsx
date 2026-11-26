import {
	IconBrandTelegram,
	IconExternalLink,
	IconLoader2,
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import type { TelegramLink } from '@/modules/auth/api/auth.api';
import { useAuth } from '@/modules/auth/hooks/use-auth';
import {
	useCreateTelegramLinkMutation,
	useUnlinkTelegramMutation,
} from '@/modules/auth/hooks/use-auth-mutations';
import { useTelegramLinkStatusQuery } from '@/modules/auth/hooks/use-auth-queries';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button, buttonVariants } from '@/modules/ui/components/button';
import {
	Dialog,
	DialogBody,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from '@/modules/ui/components/dialog';
import { toast } from '@/modules/ui/components/toast';

type TelegramLinkDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
};

/**
 * Vincula el chat de Telegram de la persona: ahí le llegan las señales por
 * aprobar con botones Aprobar / Rechazar. El enlace es de un solo uso.
 */
export function TelegramLinkDialog({
	open,
	onOpenChange,
}: TelegramLinkDialogProps) {
	const { user, refreshUser } = useAuth();
	const createLink = useCreateTelegramLinkMutation();
	const unlink = useUnlinkTelegramMutation();
	const [link, setLink] = useState<TelegramLink | null>(null);
	const linked = !!user?.telegram_linked;
	// Con el modo de respuestas "off" el bot no lee el "/start": un enlace
	// nuevo nunca se completaría
	const linkable = !!user?.telegram_linkable;
	// Con el enlace abierto se revisa solo si el bot ya recibió el "/start"
	const linkStatus = useTelegramLinkStatusQuery(open && !!link && !linked);
	const detectedLinked = linkStatus.data === true;
	// Solo la revisión que pide la persona deshabilita el botón: la automática
	// (cada pocos segundos) no debe hacerlo parpadear
	const [checking, setChecking] = useState(false);

	// El bot ya vinculó el chat: se recarga el perfil para que todo el front
	// (menú, diálogos de agentes) vea `telegram_linked`
	useEffect(() => {
		if (detectedLinked && !linked) void refreshUser();
	}, [detectedLinked, linked, refreshUser]);

	useEffect(() => {
		if (linked && link) {
			setLink(null);
			toast.add({ title: 'Telegram vinculado', type: 'success' });
		}
	}, [linked, link]);

	function handleOpenChange(next: boolean) {
		if (!next) setLink(null);
		onOpenChange(next);
	}

	async function checkNow() {
		setChecking(true);
		const { data: isLinked } = await linkStatus
			.refetch()
			.finally(() => setChecking(false));
		if (isLinked) return;
		toast.add({
			title: 'Aún no vemos el vínculo',
			description:
				'Si ya pulsaste Iniciar en Telegram, espera unos segundos: puede tardar hasta un minuto.',
			type: 'info',
		});
	}

	function generate() {
		createLink.mutate(undefined, {
			onSuccess: setLink,
			onError: (error) =>
				toast.add({
					title: 'No pudimos crear el enlace',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	function handleUnlink() {
		unlink.mutate(undefined, {
			onSuccess: () =>
				toast.add({ title: 'Telegram desvinculado', type: 'success' }),
			onError: (error) =>
				toast.add({
					title: 'No pudimos desvincular Telegram',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Dialog open={open} onOpenChange={handleOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Telegram</DialogTitle>
					<DialogDescription>
						Recibe en tu celular las señales de los agentes en modo Con
						aprobación y apruébalas o descártalas con un toque.
					</DialogDescription>
				</DialogHeader>
				<DialogBody className="flex flex-col gap-4 text-sm">
					{linked ? (
						<p>Tu chat de Telegram está vinculado.</p>
					) : link ? (
						<>
							<ol className="flex list-decimal flex-col gap-1 pl-5 text-muted-foreground">
								<li>Abre el enlace en el celular o computador con Telegram.</li>
								<li>Pulsa Iniciar en el chat del bot.</li>
								<li>Vuelve aquí: lo detectamos solos en menos de un minuto.</li>
							</ol>
							<a
								href={link.link_url}
								target="_blank"
								rel="noreferrer"
								className={buttonVariants({ variant: 'outline' })}
							>
								<IconBrandTelegram />
								Abrir Telegram
								<IconExternalLink />
							</a>
							<p className="text-xs text-muted-foreground">
								El enlace sirve una sola vez y vence en 10 minutos.
							</p>
						</>
					) : (
						<p className="text-muted-foreground">
							{linkable
								? 'Genera un enlace de un solo uso para conectar tu chat.'
								: 'Por ahora no se pueden conectar chats: el bot de Telegram no está leyendo mensajes. Pídele al administrador que active sus respuestas en Notificaciones.'}
						</p>
					)}
				</DialogBody>
				<DialogFooter>
					{linked ? (
						<Button
							variant="outline"
							disabled={unlink.isPending}
							onClick={handleUnlink}
						>
							{unlink.isPending && <IconLoader2 className="animate-spin" />}
							Desvincular
						</Button>
					) : link ? (
						<Button disabled={checking} onClick={() => void checkNow()}>
							Ya lo vinculé
						</Button>
					) : (
						<Button
							disabled={!linkable || createLink.isPending}
							onClick={generate}
						>
							{createLink.isPending ? (
								<IconLoader2 className="animate-spin" />
							) : (
								<IconBrandTelegram />
							)}
							Generar enlace
						</Button>
					)}
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
