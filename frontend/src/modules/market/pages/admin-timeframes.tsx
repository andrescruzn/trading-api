import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2, IconPlus } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type { Timeframe } from '@/modules/market/api/market.api';
import { useCreateTimeframeMutation } from '@/modules/market/hooks/use-market-mutations';
import { useTimeframesQuery } from '@/modules/market/hooks/use-market-queries';
import { describeSeconds } from '@/modules/market/lib/market-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
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
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

const columns: DataTableColumn<Timeframe>[] = [
	{ id: 'id', header: 'ID', className: 'w-16 font-mono', cell: (row) => row.id },
	{
		id: 'code',
		header: 'Código',
		cell: (row) => <span className="font-mono font-medium">{row.code}</span>,
	},
	{
		id: 'seconds',
		header: 'Segundos',
		className: 'text-right font-mono tabular-nums',
		cell: (row) => row.seconds.toLocaleString('es-CO'),
	},
	{ id: 'equals', header: 'Equivale a', cell: (row) => describeSeconds(row.seconds) },
];

const timeframeSchema = z.object({
	code: z
		.string()
		.trim()
		.min(1, 'Escribe el código')
		.max(8, 'Máximo 8 caracteres'),
	seconds: z.coerce
		.number({ message: 'Escribe un número' })
		.int('Debe ser un número entero')
		.min(1, 'Debe ser mayor que 0'),
});

type TimeframeValues = z.input<typeof timeframeSchema>;

function CreateTimeframeDialog({
	open,
	onOpenChange,
}: {
	open: boolean;
	onOpenChange: (open: boolean) => void;
}) {
	const createMutation = useCreateTimeframeMutation();
	const form = useForm<TimeframeValues, unknown, z.output<typeof timeframeSchema>>({
		resolver: zodResolver(timeframeSchema),
		defaultValues: { code: '', seconds: '' },
	});

	useEffect(() => {
		if (open) form.reset({ code: '', seconds: '' });
	}, [open, form]);

	function handleSubmit(values: z.output<typeof timeframeSchema>) {
		createMutation.mutate(values, {
			onSuccess: () => {
				toast.add({ title: 'Timeframe creado', type: 'success' });
				onOpenChange(false);
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos crear el timeframe',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Nuevo timeframe</DialogTitle>
					<DialogDescription>
						Intervalo de las velas, con el código que usa ccxt.
					</DialogDescription>
				</DialogHeader>
				<form
					id="timeframe-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="code"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="timeframe-code" required>
											Código
										</FieldLabel>
										<Input
											{...field}
											id="timeframe-code"
											placeholder="4h"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>Ej.: 1m, 5m, 15m, 1h, 4h, 1d.</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="seconds"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="timeframe-seconds" required>
											Duración en segundos
										</FieldLabel>
										<Input
											{...field}
											value={String(field.value ?? '')}
											id="timeframe-seconds"
											type="number"
											inputMode="numeric"
											placeholder="14400"
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button type="submit" form="timeframe-form" disabled={createMutation.isPending}>
						{createMutation.isPending && <IconLoader2 className="animate-spin" />}
						Crear timeframe
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}

export function AdminTimeframesPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Timeframes' }]);
	const timeframesQuery = useTimeframesQuery();
	const [creating, setCreating] = useState(false);

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Timeframes"
				description="Intervalos de vela disponibles para descargar y analizar."
				actions={[
					{ label: 'Nuevo timeframe', icon: <IconPlus />, onClick: () => setCreating(true) },
				]}
			/>
			<DataTable
				columns={columns}
				rows={timeframesQuery.data}
				getRowId={(row) => row.id}
				isLoading={timeframesQuery.isLoading}
				error={timeframesQuery.error}
				errorTitle="No pudimos cargar los timeframes"
				empty="Aún no hay timeframes. Crea el primero."
			/>
			<CreateTimeframeDialog open={creating} onOpenChange={setCreating} />
		</div>
	);
}
