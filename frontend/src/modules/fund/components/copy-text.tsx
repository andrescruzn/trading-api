import { IconCheck, IconCopy } from '@tabler/icons-react';
import { useState } from 'react';
import { Button } from '@/modules/ui/components/button';
import { toast } from '@/modules/ui/components/toast';
import { cn } from '@/modules/ui/lib/utils';

type CopyTextProps = {
	value: string;
	/** Nombre de lo que se copia, para el aviso ("Dirección copiada"). */
	label: string;
	/** Muestra el valor completo (direcciones) o recortado (txid en tablas). */
	truncate?: boolean;
	className?: string;
};

/**
 * Texto monoespaciado con botón de copiar. Copiar en vez de tipear evita
 * mandar dinero a una dirección equivocada.
 */
export function CopyText({
	value,
	label,
	truncate = false,
	className,
}: CopyTextProps) {
	const [copied, setCopied] = useState(false);

	async function copy(event: React.MouseEvent) {
		// Puede estar dentro de una fila clicable
		event.stopPropagation();
		try {
			await navigator.clipboard.writeText(value);
			setCopied(true);
			toast.add({ title: `${label} copiado`, type: 'success' });
			window.setTimeout(() => setCopied(false), 2000);
		} catch {
			toast.add({
				title: 'No pudimos copiar',
				description: 'Selecciona el texto y cópialo a mano.',
				type: 'error',
			});
		}
	}

	return (
		<span className={cn('inline-flex min-w-0 items-center gap-1', className)}>
			<span
				className={cn('font-mono text-sm', truncate ? 'truncate' : 'break-all')}
				title={value}
			>
				{truncate && value.length > 16
					? `${value.slice(0, 8)}…${value.slice(-6)}`
					: value}
			</span>
			<Button
				type="button"
				variant="ghost"
				size="icon-xs"
				onClick={copy}
				aria-label={`Copiar ${label.toLowerCase()}`}
			>
				{copied ? <IconCheck /> : <IconCopy />}
			</Button>
		</span>
	);
}
