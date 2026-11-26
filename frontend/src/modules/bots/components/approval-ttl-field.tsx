import { IconLoader2 } from '@tabler/icons-react';
import { type FormEvent, useState } from 'react';
import type { Bot } from '@/modules/bots/api/bots.api';
import { useUpdateBotMutation } from '@/modules/bots/hooks/use-bots-mutations';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button } from '@/modules/ui/components/button';
import {
	Field,
	FieldDescription,
	FieldError,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

// Mismos límites que el backend (UpdateBotRequest: 1–1440)
const MIN_MINUTES = 1;
const MAX_MINUTES = 1440;

/** Vacío = valor del servidor; si no, entero entre 1 y 1440. */
function parseMinutes(raw: string): { value: number | null; error?: string } {
	const text = raw.trim();
	if (!text) return { value: null };
	const number = Number(text);
	if (
		!Number.isInteger(number) ||
		number < MIN_MINUTES ||
		number > MAX_MINUTES
	) {
		return {
			value: null,
			error: 'Escribe un número entero de minutos entre 1 y 1.440 (24 horas).',
		};
	}
	return { value: number };
}

/**
 * Minutos que tiene la persona para aprobar una señal antes de que venza
 * (modo Con aprobación). Vacío vuelve al valor por defecto del servidor.
 */
export function ApprovalTtlField({ bot }: { bot: Bot }) {
	const mutation = useUpdateBotMutation();
	const [raw, setRaw] = useState(
		bot.approval_ttl_minutes !== null ? String(bot.approval_ttl_minutes) : '',
	);
	const [error, setError] = useState<string | undefined>();

	function handleSubmit(event: FormEvent) {
		event.preventDefault();
		const parsed = parseMinutes(raw);
		setError(parsed.error);
		if (parsed.error) return;

		mutation.mutate(
			{ id: bot.id, input: { approval_ttl_minutes: parsed.value } },
			{
				onSuccess: () =>
					toast.add({ title: 'Tiempo para aprobar guardado', type: 'success' }),
				onError: (mutationError) =>
					toast.add({
						title: 'No pudimos guardar el tiempo',
						description: getErrorMessage(mutationError),
						type: 'error',
					}),
			},
		);
	}

	return (
		<form onSubmit={handleSubmit} noValidate className="flex flex-col gap-2">
			<Field data-invalid={!!error}>
				<FieldLabel htmlFor="approval-ttl">Minutos para aprobar</FieldLabel>
				<div className="flex max-w-sm gap-2">
					<Input
						id="approval-ttl"
						inputMode="numeric"
						placeholder="Por defecto del servidor"
						value={raw}
						aria-invalid={!!error}
						onChange={(event) => setRaw(event.target.value)}
					/>
					<Button type="submit" variant="outline" disabled={mutation.isPending}>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Guardar
					</Button>
				</div>
				<FieldDescription>
					Si nadie decide antes, la señal vence y no se ejecuta. Déjalo vacío
					para usar el valor por defecto.
				</FieldDescription>
				{error && <FieldError errors={[{ message: error }]} />}
			</Field>
		</form>
	);
}
