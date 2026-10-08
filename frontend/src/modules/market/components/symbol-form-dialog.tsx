import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { AssetClass, MarketSymbol } from '@/modules/market/api/market.api';
import {
	useCreateSymbolMutation,
	useUpdateSymbolMutation,
} from '@/modules/market/hooks/use-market-mutations';
import { useExchangesQuery } from '@/modules/market/hooks/use-market-queries';
import { ASSET_CLASS_OPTIONS } from '@/modules/market/lib/market-labels';
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
	FieldDescription,
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

const optionalDecimal = z
	.string()
	.trim()
	.refine(
		(value) => value === '' || Number(value) > 0,
		'Debe ser un número mayor que 0',
	);

const symbolSchema = z.object({
	exchange_id: requiredSelectField('Elige el exchange'),
	symbol: z.string().trim().min(1, 'Escribe el símbolo').max(64),
	asset_class: requiredSelectField('Elige la clase de activo'),
	base_asset: z.string().trim().max(32),
	quote_asset: z.string().trim().max(32),
	tick_size: optionalDecimal,
	lot_size: optionalDecimal,
	is_active: z.boolean(),
});

type SymbolFormInput = z.input<typeof symbolSchema>;
type SymbolFormOutput = z.output<typeof symbolSchema>;

type SymbolFormDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	/** `null` = crear; un símbolo = editar (exchange y símbolo no se cambian). */
	symbol: MarketSymbol | null;
};

const emptyToNull = (value: string) => (value === '' ? null : value);

export function SymbolFormDialog({
	open,
	onOpenChange,
	symbol,
}: SymbolFormDialogProps) {
	const isEdit = !!symbol;
	const exchangesQuery = useExchangesQuery({ is_active: true });
	const createMutation = useCreateSymbolMutation();
	const updateMutation = useUpdateSymbolMutation();
	const isPending = createMutation.isPending || updateMutation.isPending;

	const form = useForm<SymbolFormInput, unknown, SymbolFormOutput>({
		resolver: zodResolver(symbolSchema),
		defaultValues: {
			exchange_id: null,
			symbol: '',
			asset_class: null,
			base_asset: '',
			quote_asset: '',
			tick_size: '',
			lot_size: '',
			is_active: true,
		},
	});

	useEffect(() => {
		if (!open) return;
		form.reset({
			exchange_id: symbol ? String(symbol.exchange_id) : null,
			symbol: symbol?.symbol ?? '',
			asset_class: symbol?.asset_class ?? null,
			base_asset: symbol?.base_asset ?? '',
			quote_asset: symbol?.quote_asset ?? '',
			tick_size: symbol?.tick_size ?? '',
			lot_size: symbol?.lot_size ?? '',
			is_active: symbol?.is_active ?? true,
		});
	}, [open, symbol, form]);

	// Al escribir `BTC/USDT` se sugieren base y cotización si están vacías.
	function handleSymbolBlur(value: string) {
		const [base, quote] = value.toUpperCase().split('/');
		if (base && quote) {
			if (!form.getValues('base_asset')) form.setValue('base_asset', base);
			if (!form.getValues('quote_asset')) form.setValue('quote_asset', quote);
		}
	}

	function handleSubmit(values: SymbolFormOutput) {
		const shared = {
			asset_class: values.asset_class as AssetClass,
			base_asset: emptyToNull(values.base_asset),
			quote_asset: emptyToNull(values.quote_asset),
			tick_size: emptyToNull(values.tick_size),
			lot_size: emptyToNull(values.lot_size),
		};
		const callbacks = {
			onSuccess: () => {
				toast.add({
					title: isEdit ? 'Símbolo actualizado' : 'Símbolo creado',
					type: 'success',
				});
				onOpenChange(false);
			},
			onError: (error: unknown) =>
				toast.add({
					title: isEdit
						? 'No pudimos actualizar el símbolo'
						: 'No pudimos crear el símbolo',
					description: getErrorMessage(error),
					type: 'error',
				}),
		};

		if (symbol) {
			updateMutation.mutate(
				{ id: symbol.id, input: { ...shared, is_active: values.is_active } },
				callbacks,
			);
		} else {
			createMutation.mutate(
				{
					...shared,
					exchange_id: Number(values.exchange_id),
					symbol: values.symbol.toUpperCase(),
				},
				callbacks,
			);
		}
	}

	const exchangeOptions = (exchangesQuery.data ?? []).map((exchange) => ({
		value: String(exchange.id),
		label: exchange.name,
	}));

	const textFields: {
		name: 'base_asset' | 'quote_asset' | 'tick_size' | 'lot_size';
		label: string;
		placeholder: string;
	}[] = [
		{ name: 'base_asset', label: 'Activo base', placeholder: 'BTC' },
		{ name: 'quote_asset', label: 'Activo de cotización', placeholder: 'USDT' },
		{ name: 'tick_size', label: 'Tick size', placeholder: '0.01' },
		{ name: 'lot_size', label: 'Lot size', placeholder: '0.00001' },
	];

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle>
						{isEdit ? 'Editar símbolo' : 'Nuevo símbolo'}
					</DialogTitle>
					<DialogDescription>
						{symbol
							? `${symbol.symbol} · ${symbol.exchange_name ?? ''}`
							: 'Par o activo que el sistema puede descargar y operar.'}
					</DialogDescription>
				</DialogHeader>
				<form
					id="symbol-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							{!isEdit && (
								<>
									<Controller
										name="exchange_id"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="symbol-exchange" required>
													Exchange
												</FieldLabel>
												<OptionSelect
													id="symbol-exchange"
													value={field.value}
													onChange={field.onChange}
													options={exchangeOptions}
													aria-invalid={fieldState.invalid}
												/>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
									<Controller
										name="symbol"
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor="symbol-symbol" required>
													Símbolo
												</FieldLabel>
												<Input
													{...field}
													id="symbol-symbol"
													placeholder="BTC/USDT"
													aria-invalid={fieldState.invalid}
													onBlur={(event) => {
														field.onBlur();
														handleSymbolBlur(event.target.value);
													}}
												/>
												<FieldDescription>
													Tal como lo nombra el exchange (formato ccxt).
												</FieldDescription>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
								</>
							)}
							<Controller
								name="asset_class"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="symbol-class" required>
											Clase de activo
										</FieldLabel>
										<OptionSelect
											id="symbol-class"
											value={field.value}
											onChange={field.onChange}
											options={ASSET_CLASS_OPTIONS}
											aria-invalid={fieldState.invalid}
										/>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<div className="grid gap-4 sm:grid-cols-2">
								{textFields.map((item) => (
									<Controller
										key={item.name}
										name={item.name}
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor={`symbol-${item.name}`}>
													{item.label}
												</FieldLabel>
												<Input
													{...field}
													id={`symbol-${item.name}`}
													placeholder={item.placeholder}
													aria-invalid={fieldState.invalid}
												/>
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
								))}
							</div>
							{isEdit && (
								<Controller
									name="is_active"
									control={form.control}
									render={({ field }) => (
										<Field orientation="horizontal">
											<Checkbox
												id="symbol-active"
												checked={field.value}
												onCheckedChange={(checked) => field.onChange(checked)}
											/>
											<FieldLabel htmlFor="symbol-active">Activo</FieldLabel>
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
					<Button type="submit" form="symbol-form" disabled={isPending}>
						{isPending && <IconLoader2 className="animate-spin" />}
						{isEdit ? 'Guardar cambios' : 'Crear símbolo'}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
