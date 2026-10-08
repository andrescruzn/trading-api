import { IconAlertCircle } from '@tabler/icons-react';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';

type ErrorAlertProps = {
	/** Ej. `No pudimos cargar los bots`. */
	title: string;
	error: unknown;
	className?: string;
};

/** Error de carga inline: título fijo + mensaje que devolvió la API. */
export function ErrorAlert({ title, error, className }: ErrorAlertProps) {
	return (
		<Alert variant="destructive" className={className}>
			<IconAlertCircle />
			<AlertTitle>{title}</AlertTitle>
			<AlertDescription>{getErrorMessage(error)}</AlertDescription>
		</Alert>
	);
}
