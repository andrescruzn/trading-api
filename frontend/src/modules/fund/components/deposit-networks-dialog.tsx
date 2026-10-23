import { IconLoader2, IconPlus, IconTrash } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import type {
	DepositNetworkConfig,
	NetworkChoice,
} from '@/modules/fund/api/fund.api';
import { useSetDepositNetworksMutation } from '@/modules/fund/hooks/use-fund-mutations';
import { useAvailableNetworksQuery } from '@/modules/fund/hooks/use-fund-queries';
import { ErrorAlert } from '@/modules/shared/components/error-alert';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button } from '@/modules/ui/components/button';
import { Checkbox } from '@/modules/ui/components/checkbox';
import {
	Dialog,
	DialogBody,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from '@/modules/ui/components/dialog';
import { Field, FieldLabel } from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { Skeleton } from '@/modules/ui/components/skeleton';
import { toast } from '@/modules/ui/components/toast';

type DepositNetworksDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	current: DepositNetworkConfig[];
};

type ManualRow = {
	network: string;
	name: string;
	address: string;
	tag: string;
};

const EMPTY_ROW: ManualRow = { network: '', name: '', address: '', tag: '' };

/**
 * Elige las redes por las que se puede depositar. Con billetera live, la
 * dirección se lee del exchange (nunca se escribe a mano); con billetera de
 * práctica no hay exchange, así que se escribe solo para probar el flujo.
 */
export function DepositNetworksDialog({
	open,
	onOpenChange,
	current,
}: DepositNetworksDialogProps) {
	const availableQuery = useAvailableNetworksQuery(open);
	const mutation = useSetDepositNetworksMutation();
	const [selected, setSelected] = useState<string[]>([]);
	const [manual, setManual] = useState<ManualRow[]>([]);

	useEffect(() => {
		if (!open) return;
		setSelected(current.map((network) => network.network));
		setManual(
			current.length
				? current.map((n) => ({ ...n, tag: n.tag ?? '' }))
				: [{ ...EMPTY_ROW }],
		);
	}, [open, current]);

	const isLive = availableQuery.data?.is_live ?? false;
	const asset = availableQuery.data?.asset ?? 'USDT';

	function toggle(code: string, checked: boolean) {
		setSelected((prev) =>
			checked ? [...prev, code] : prev.filter((item) => item !== code),
		);
	}

	function updateRow(index: number, patch: Partial<ManualRow>) {
		setManual((rows) =>
			rows.map((row, i) => (i === index ? { ...row, ...patch } : row)),
		);
	}

	function save() {
		const networks: NetworkChoice[] = isLive
			? selected.map((network) => ({ network }))
			: manual
					.filter((row) => row.network.trim())
					.map((row) => ({
						network: row.network.trim(),
						name: row.name.trim() || null,
						address: row.address.trim(),
						tag: row.tag.trim() || null,
					}));
		mutation.mutate(networks, {
			onSuccess: () => {
				toast.add({
					title: 'Redes guardadas',
					description: isLive
						? 'Las direcciones se leyeron del exchange.'
						: undefined,
					type: 'success',
				});
				onOpenChange(false);
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos guardar las redes',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-xl">
				<DialogHeader>
					<DialogTitle>Redes de depósito</DialogTitle>
					<DialogDescription>
						{isLive
							? `Por qué redes se puede enviar ${asset} a la billetera. La dirección de cada una se lee del exchange al guardar.`
							: 'Billetera de práctica: escribe la red y una dirección de prueba. En una billetera live la dirección se lee del exchange.'}
					</DialogDescription>
				</DialogHeader>
				<DialogBody>
					{availableQuery.isLoading ? (
						<div className="flex flex-col gap-2">
							<Skeleton className="h-6 w-full" />
							<Skeleton className="h-6 w-full" />
							<Skeleton className="h-6 w-2/3" />
						</div>
					) : availableQuery.error ? (
						<ErrorAlert
							title="No pudimos leer las redes del exchange"
							error={availableQuery.error}
						/>
					) : isLive ? (
						<div className="flex flex-col gap-3">
							{(availableQuery.data?.networks ?? []).map((network) => (
								<Field key={network.code} orientation="horizontal">
									<Checkbox
										id={`network-${network.code}`}
										checked={selected.includes(network.code)}
										disabled={!network.deposit_enabled}
										onCheckedChange={(checked) =>
											toggle(network.code, checked === true)
										}
									/>
									<FieldLabel htmlFor={`network-${network.code}`}>
										{network.name}{' '}
										<span className="text-muted-foreground">
											({network.code})
											{!network.deposit_enabled &&
												' · el exchange no acepta depósitos hoy'}
										</span>
									</FieldLabel>
								</Field>
							))}
						</div>
					) : (
						<div className="flex flex-col gap-4">
							{manual.map((row, index) => (
								// Las filas no tienen id estable mientras se escriben: se usa el índice
								<div
									key={index}
									className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]"
								>
									<Input
										aria-label="Código de la red"
										placeholder="TRC20"
										value={row.network}
										onChange={(event) =>
											updateRow(index, { network: event.target.value })
										}
									/>
									<Input
										aria-label="Nombre de la red"
										placeholder="Tron"
										value={row.name}
										onChange={(event) =>
											updateRow(index, { name: event.target.value })
										}
									/>
									<Button
										variant="ghost"
										size="icon"
										aria-label="Quitar red"
										onClick={() =>
											setManual((rows) => rows.filter((_, i) => i !== index))
										}
									>
										<IconTrash />
									</Button>
									<Input
										className="font-mono sm:col-span-2"
										aria-label="Dirección"
										placeholder="Dirección de prueba"
										value={row.address}
										onChange={(event) =>
											updateRow(index, { address: event.target.value })
										}
									/>
								</div>
							))}
							<Button
								variant="outline"
								size="sm"
								className="self-start"
								onClick={() => setManual((rows) => [...rows, { ...EMPTY_ROW }])}
							>
								<IconPlus />
								Agregar red
							</Button>
						</div>
					)}
				</DialogBody>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button
						onClick={save}
						disabled={mutation.isPending || availableQuery.isLoading}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Guardar redes
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
