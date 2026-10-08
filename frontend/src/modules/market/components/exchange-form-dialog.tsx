import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { Exchange, ExchangeType } from '@/modules/market/api/market.api';
import {
	useCreateExchangeMutation,
	useUpdateExchangeMutation,
} from '@/modules/market/hooks/use-market-mutations';
import { EXCHANGE_TYPE_OPTIONS } from '@/modules/market/lib/market-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
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
import {
	Field,
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

const exchangeSchema = z.object({
	name: z.string().trim().min(1, 'Escribe el nombre').max(120),
	type: requiredSelectField('Elige el tipo'),
	is_active: z.boolean(),
});

type ExchangeValues = z.infer<typeof exchangeSchema>;

type ExchangeFormDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	/** `null` = crear; un exchange = editar. */
	exchange: Exchange | null;
};

export function ExchangeFormDialog({
	open,
	onOpenChange,
	exchange,
}: ExchangeFormDialogProps) {
	const isEdit = !!exchange;
	const createMutation = useCreateExchangeMutation();
	const updateMutation = useUpdateExchangeMutation();
	const isPending = createMutation.isPending || updateMutation.isPending;

	const form = useForm<ExchangeValues>({
		resolver: zodResolver(exchangeSchema),
		defaultValues: { name: '', type: null, is_active: true },
	});

	// Cada vez que se abre, el formulario arranca con los datos del exchange
	// a editar (o vacío al crear).
	useEffect(() => {
		if (!open) return;
		form.reset({
			name: exchange?.name ?? '',
			type: exchange?.type ?? null,
			is_active: exchange?.is_active ?? true,
		});
	}, [open, exchange, form]);

	function handleSubmit(values: ExchangeValues) {
		const input = { name: values.name, type: values.type as ExchangeType };
		const callbacks = {
			onSuccess: () => {
				toast.add({
					title: isEdit ? 'Exchange actualizado' : 'Exchange creado',
					type: 'success',
				});
				onOpenChange(false);
			},
			onError: (error: unknown) =>
				toast.add({
					title: isEdit
						? 'No pudimos actualizar el exchange'
						: 'No pudimos crear el exchange',
					description: getErrorMessage(error),
					type: 'error',
				}),
		};

		if (exchange) {
			updateMutation.mutate(
				{ id: exchange.id, input: { ...input, is_active: values.is_active } },
				callbacks,
			);
		} else {
			createMutation.mutate(input, callbacks);
		}
	}

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>
						{isEdit ? 'Editar exchange' : 'Nuevo exchange'}
					</DialogTitle>
					<DialogDescription>
						Fuente de datos de mercado o lugar donde se ejecutan las órdenes.
					</DialogDescription>
				</DialogHeader>
				<form
					id="exchange-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<Controller
								name="name"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="exchange-name" required>
											Nombre
										</FieldLabel>
										<Input
											{...field}
											id="exchange-name"
											placeholder="binance"
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="type"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="exchange-type" required>
											Tipo
										</FieldLabel>
										<OptionSelect
											id="exchange-type"
											value={field.value}
											onChange={field.onChange}
											options={EXCHANGE_TYPE_OPTIONS}
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							{isEdit && (
								<Controller
									name="is_active"
									control={form.control}
									render={({ field }) => (
										<Field orientation="horizontal">
											<Checkbox
												id="exchange-active"
												checked={field.value}
												onCheckedChange={(checked) => field.onChange(checked)}
											/>
											<FieldLabel htmlFor="exchange-active">Activo</FieldLabel>
										</Field>
									)}
								/>
							)}
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button type="submit" form="exchange-form" disabled={isPending}>
						{isPending && <IconLoader2 className="animate-spin" />}
						{isEdit ? 'Guardar cambios' : 'Crear exchange'}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
