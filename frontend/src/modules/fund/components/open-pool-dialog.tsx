import { IconLoader2 } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useOpenPoolMutation } from '@/modules/fund/hooks/use-fund-pools-mutations';
import { useEligibleAgentsQuery } from '@/modules/fund/hooks/use-fund-pools-queries';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button } from '@/modules/ui/components/button';
import {
	Dialog,
	DialogBody,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from '@/modules/ui/components/dialog';
import {
	Field,
	FieldDescription,
	FieldLabel,
} from '@/modules/ui/components/field';
import { toast } from '@/modules/ui/components/toast';

type OpenPoolDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	onOpened: (poolId: number) => void;
};

/** Un super admin abre un agente de la billetera para que reciba dinero del fondo. */
export function OpenPoolDialog({
	open,
	onOpenChange,
	onOpened,
}: OpenPoolDialogProps) {
	const eligibleQuery = useEligibleAgentsQuery(open);
	const mutation = useOpenPoolMutation();
	const [botId, setBotId] = useState<string | null>(null);

	useEffect(() => {
		if (open) setBotId(null);
	}, [open]);

	const options = (eligibleQuery.data ?? []).map((agent) => ({
		value: String(agent.bot_id),
		label: `${agent.name}${agent.symbol ? ` · ${agent.symbol}` : ''}`,
	}));

	function save() {
		if (!botId) return;
		mutation.mutate(Number(botId), {
			onSuccess: (pool) => {
				toast.add({
					title: 'Agente abierto al fondo',
					description:
						'Asígnale dinero y liquídalo para que empiece a operarlo.',
					type: 'success',
				});
				onOpenChange(false);
				onOpened(pool.id);
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos abrir el agente',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Abrir un agente al fondo</DialogTitle>
					<DialogDescription>
						El agente pasa a operar con el dinero que le asignes a cada
						participante. Lo que operó antes no cuenta.
					</DialogDescription>
				</DialogHeader>
				<DialogBody>
					<Field>
						<FieldLabel htmlFor="open-pool-agent" required>
							Agente
						</FieldLabel>
						<OptionSelect
							id="open-pool-agent"
							value={botId}
							onChange={setBotId}
							options={options}
							placeholder={
								eligibleQuery.isLoading
									? 'Cargando agentes…'
									: 'Elige un agente'
							}
							disabled={eligibleQuery.isLoading || options.length === 0}
						/>
						<FieldDescription>
							{options.length === 0 && !eligibleQuery.isLoading
								? 'No hay agentes para abrir: deben ser agentes reales (no demo), con un par en USDT, y no estar ya en el fondo.'
								: 'Solo aparecen agentes reales con un par en USDT. Los agentes demo no usan el dinero del fondo.'}
						</FieldDescription>
					</Field>
				</DialogBody>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button onClick={save} disabled={!botId || mutation.isPending}>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Abrir al fondo
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
