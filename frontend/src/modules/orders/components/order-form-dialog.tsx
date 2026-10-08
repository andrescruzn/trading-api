import { zodResolver } from '@hookform/resolvers/zod';
import { IconAlertTriangle, IconLoader2 } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import type { Bot } from '@/modules/bots/api/bots.api';
import type {
	OrderInput,
	OrderSide,
	OrderType,
} from '@/modules/orders/api/orders.api';
import { useCreateOrderMutation } from '@/modules/orders/hooks/use-orders-mutations';
import {
	ORDER_SIDE_LABELS,
	ORDER_SIDE_OPTIONS,
	ORDER_TYPE_LABELS,
	ORDER_TYPE_OPTIONS,
	orderNeedsPrice,
	orderNeedsStopPrice,
} from '@/modules/orders/lib/orders-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { formatNumber, formatPrice } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
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

/** Acepta `0,5` además de `0.5`; el backend espera punto decimal. */
function normalizeDecimal(value: string): string {
	return value.trim().replace(',', '.');
}

function isPositiveDecimal(value: string): boolean {
	const normalized = normalizeDecimal(value);
	return normalized !== '' && Number(normalized) > 0;
}

const orderSchema = z
	.object({
		side: requiredSelectField('Elige el lado'),
		type: requiredSelectField('Elige el tipo de orden'),
		qty: z
			.string()
			.refine(isPositiveDecimal, 'Escribe una cantidad mayor que 0'),
		price: z.string(),
		stop_price: z.string(),
	})
	.superRefine((values, ctx) => {
		if (orderNeedsPrice(values.type) && !isPositiveDecimal(values.price)) {
			ctx.addIssue({
				code: 'custom',
				path: ['price'],
				message: 'Escribe un precio límite mayor que 0',
			});
		}
		if (
			orderNeedsStopPrice(values.type) &&
			!isPositiveDecimal(values.stop_price)
		) {
			ctx.addIssue({
				code: 'custom',
				path: ['stop_price'],
				message: 'Escribe un precio stop mayor que 0',
			});
		}
	});

type OrderValues = z.output<typeof orderSchema>;

const DEFAULT_VALUES: z.input<typeof orderSchema> = {
	side: 'buy',
	type: 'market',
	qty: '',
	price: '',
	stop_price: '',
};

type OrderFormDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	/** Bot al que se envía la orden (el elegido en la página). */
	bot: Bot | null;
	/** Ej. `#12 · BTC/USDT · 4h`. */
	botLabel: string;
};

export function OrderFormDialog({
	open,
	onOpenChange,
	bot,
	botLabel,
}: OrderFormDialogProps) {
	const createMutation = useCreateOrderMutation();
	// Orden live a la espera de confirmación explícita.
	const [pendingLive, setPendingLive] = useState<OrderInput | null>(null);
	const isLive = bot?.mode === 'live';
	const isRunning = bot?.status === 'running';

	const form = useForm<z.input<typeof orderSchema>, unknown, OrderValues>({
		resolver: zodResolver(orderSchema),
		defaultValues: DEFAULT_VALUES,
	});
	const type = useWatch({ control: form.control, name: 'type' });

	useEffect(() => {
		if (!open) return;
		form.reset(DEFAULT_VALUES);
		setPendingLive(null);
	}, [open, form]);

	function sendOrder(input: OrderInput) {
		createMutation.mutate(input, {
			onSuccess: () => {
				toast.add({ title: 'Orden ejecutada', type: 'success' });
				setPendingLive(null);
				onOpenChange(false);
			},
			onError: (error) =>
				toast.add({
					title: 'No pudimos ejecutar la orden',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	function handleSubmit(values: OrderValues) {
		if (!bot) return;
		const input: OrderInput = {
			bot_id: bot.id,
			side: values.side as OrderSide,
			type: values.type as OrderType,
			qty: normalizeDecimal(values.qty),
			// Solo se envían los precios que pide el tipo: el backend rechaza
			// un precio límite en una orden de mercado.
			...(orderNeedsPrice(values.type) && {
				price: normalizeDecimal(values.price),
			}),
			...(orderNeedsStopPrice(values.type) && {
				stop_price: normalizeDecimal(values.stop_price),
			}),
		};
		if (isLive) {
			setPendingLive(input);
			return;
		}
		sendOrder(input);
	}

	const priceFields: {
		name: 'price' | 'stop_price';
		label: string;
		placeholder: string;
	}[] = [
		...(orderNeedsPrice(type)
			? [
					{
						name: 'price' as const,
						label: 'Precio límite',
						placeholder: '65000',
					},
				]
			: []),
		...(orderNeedsStopPrice(type)
			? [
					{
						name: 'stop_price' as const,
						label: 'Precio stop',
						placeholder: '64000',
					},
				]
			: []),
	];

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle>Nueva orden</DialogTitle>
					<DialogDescription>
						Bot {botLabel}. La orden se ejecuta al enviarla.
					</DialogDescription>
				</DialogHeader>
				<form
					id="order-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							{isLive && (
								<Alert variant="destructive">
									<IconAlertTriangle />
									<AlertTitle>Modo live: dinero real</AlertTitle>
									<AlertDescription>
										Esta orden se envía al exchange con tu dinero. Te pediremos
										confirmarla.
									</AlertDescription>
								</Alert>
							)}
							{bot && !isRunning && (
								<Alert>
									<IconAlertTriangle />
									<AlertTitle>El bot no está activo</AlertTitle>
									<AlertDescription>
										Solo los bots activos aceptan órdenes. Inícialo desde Bots.
									</AlertDescription>
								</Alert>
							)}
							<div className="grid gap-4 sm:grid-cols-2">
								<Controller
									name="side"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="order-side" required>
												Lado
											</FieldLabel>
											<OptionSelect
												id="order-side"
												value={field.value}
												onChange={field.onChange}
												options={ORDER_SIDE_OPTIONS}
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
											<FieldLabel htmlFor="order-type" required>
												Tipo
											</FieldLabel>
											<OptionSelect
												id="order-type"
												value={field.value}
												onChange={field.onChange}
												options={ORDER_TYPE_OPTIONS}
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							</div>
							<Controller
								name="qty"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="order-qty" required>
											Cantidad
										</FieldLabel>
										<Input
											{...field}
											id="order-qty"
											inputMode="decimal"
											placeholder="0.01"
											autoComplete="off"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											En unidades del activo base (ej.: 0.01 BTC).
										</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							{priceFields.length > 0 && (
								<div className="grid gap-4 sm:grid-cols-2">
									{priceFields.map((item) => (
										<Controller
											key={item.name}
											name={item.name}
											control={form.control}
											render={({ field, fieldState }) => (
												<Field data-invalid={fieldState.invalid}>
													<FieldLabel htmlFor={`order-${item.name}`} required>
														{item.label}
													</FieldLabel>
													<Input
														{...field}
														id={`order-${item.name}`}
														inputMode="decimal"
														placeholder={item.placeholder}
														autoComplete="off"
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
							)}
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button
						type="submit"
						form="order-form"
						variant={isLive ? 'destructive' : 'default'}
						disabled={!bot || !isRunning || createMutation.isPending}
					>
						{createMutation.isPending && (
							<IconLoader2 className="animate-spin" />
						)}
						Ejecutar orden
					</Button>
				</DialogFooter>

				{/* Dentro del diálogo para que Base UI lo trate como diálogo anidado. */}
				<AlertDialog
					open={!!pendingLive}
					onOpenChange={(next) => !next && setPendingLive(null)}
				>
					<AlertDialogContent>
						<AlertDialogHeader>
							<AlertDialogTitle>
								¿Ejecutar la orden con dinero real?
							</AlertDialogTitle>
							<AlertDialogDescription>
								El bot {botLabel} está en modo live: la orden se envía al
								exchange y no se puede deshacer.
							</AlertDialogDescription>
						</AlertDialogHeader>
						{pendingLive && (
							<dl className="grid grid-cols-2 gap-3 text-sm">
								<div>
									<dt className="text-muted-foreground">Lado</dt>
									<dd className="font-medium">
										{ORDER_SIDE_LABELS[pendingLive.side]}
									</dd>
								</div>
								<div>
									<dt className="text-muted-foreground">Tipo</dt>
									<dd className="font-medium">
										{ORDER_TYPE_LABELS[pendingLive.type]}
									</dd>
								</div>
								<div>
									<dt className="text-muted-foreground">Cantidad</dt>
									<dd className="font-mono font-medium">
										{formatNumber(pendingLive.qty)}
									</dd>
								</div>
								<div>
									<dt className="text-muted-foreground">Precio</dt>
									<dd className="font-mono font-medium">
										{pendingLive.price
											? formatPrice(pendingLive.price)
											: pendingLive.stop_price
												? `Stop ${formatPrice(pendingLive.stop_price)}`
												: 'A mercado'}
									</dd>
								</div>
							</dl>
						)}
						<AlertDialogFooter>
							<AlertDialogCancel>Cancelar</AlertDialogCancel>
							<AlertDialogAction
								variant="destructive"
								disabled={createMutation.isPending}
								onClick={() => pendingLive && sendOrder(pendingLive)}
							>
								{createMutation.isPending && (
									<IconLoader2 className="animate-spin" />
								)}
								Ejecutar orden
							</AlertDialogAction>
						</AlertDialogFooter>
					</AlertDialogContent>
				</AlertDialog>
			</DialogContent>
		</Dialog>
	);
}
