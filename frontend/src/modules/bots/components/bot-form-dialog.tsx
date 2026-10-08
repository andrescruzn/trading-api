import { zodResolver } from '@hookform/resolvers/zod';
import { IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import { useAccountsQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import type { Bot, BotMode } from '@/modules/bots/api/bots.api';
import { useCreateBotMutation } from '@/modules/bots/hooks/use-bots-mutations';
import {
	BOT_MODE_FORM_OPTIONS,
	BOT_MODE_LABELS,
} from '@/modules/bots/lib/bots-labels';
import { useFeatureSetsQuery } from '@/modules/features/hooks/use-features-queries';
import {
	useSymbolsQuery,
	useTimeframesQuery,
} from '@/modules/market/hooks/use-market-queries';
import {
	symbolOptions,
	timeframeOptions,
} from '@/modules/market/lib/market-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
import { useStrategiesQuery } from '@/modules/strategies/hooks/use-strategies-queries';
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

// Regla del 1 %: nunca arriesgar más del 1 % del capital por operación.
const MAX_RISK_PCT = 1;

const botSchema = z.object({
	account_id: requiredSelectField('Elige la cuenta'),
	symbol_id: requiredSelectField('Elige el símbolo'),
	timeframe_id: requiredSelectField('Elige el timeframe'),
	strategy_id: requiredSelectField('Elige la estrategia'),
	feature_set_id: requiredSelectField('Elige el conjunto de indicadores'),
	mode: requiredSelectField('Elige el modo'),
	risk_pct: z.coerce
		.number({ message: 'Escribe un número' })
		.gt(0, 'Debe ser mayor que 0 %')
		.max(MAX_RISK_PCT, 'Máximo 1 % del capital por operación'),
});

type BotFormInput = z.input<typeof botSchema>;
type BotFormOutput = z.output<typeof botSchema>;

const DEFAULT_VALUES: BotFormInput = {
	account_id: null,
	symbol_id: null,
	timeframe_id: null,
	strategy_id: null,
	feature_set_id: null,
	mode: 'paper',
	risk_pct: 1,
};

type BotFormDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	/** Se llama con el bot recién creado (p. ej. para seleccionarlo). */
	onCreated?: (bot: Bot) => void;
};

export function BotFormDialog({
	open,
	onOpenChange,
	onCreated,
}: BotFormDialogProps) {
	const accountsQuery = useAccountsQuery();
	const symbolsQuery = useSymbolsQuery({ is_active: true });
	const timeframesQuery = useTimeframesQuery();
	const strategiesQuery = useStrategiesQuery();
	const featureSetsQuery = useFeatureSetsQuery();
	const createMutation = useCreateBotMutation();

	const form = useForm<BotFormInput, unknown, BotFormOutput>({
		resolver: zodResolver(botSchema),
		defaultValues: DEFAULT_VALUES,
	});
	const mode = useWatch({ control: form.control, name: 'mode' });

	useEffect(() => {
		if (open) form.reset(DEFAULT_VALUES);
	}, [open, form]);

	function handleSubmit(values: BotFormOutput) {
		createMutation.mutate(
			{
				account_id: Number(values.account_id),
				symbol_id: Number(values.symbol_id),
				timeframe_id: Number(values.timeframe_id),
				strategy_id: Number(values.strategy_id),
				feature_set_id: Number(values.feature_set_id),
				mode: values.mode as BotMode,
				// En pantalla es un porcentaje; el backend lo espera como fracción.
				risk_params: { risk_pct: Number((values.risk_pct / 100).toFixed(6)) },
			},
			{
				onSuccess: (bot) => {
					toast.add({ title: 'Bot creado', type: 'success' });
					onOpenChange(false);
					onCreated?.(bot);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos crear el bot',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	const accountOptions = (accountsQuery.data ?? []).map((account) => ({
		value: String(account.id),
		label: `${account.name} · ${BOT_MODE_LABELS[account.mode] ?? account.mode}`,
	}));
	const strategyOptions = (strategiesQuery.data ?? []).map((strategy) => ({
		value: String(strategy.id),
		label: `${strategy.name} v${strategy.version}`,
	}));
	const featureSetOptions = (featureSetsQuery.data ?? []).map((featureSet) => ({
		value: String(featureSet.id),
		label: `${featureSet.name} v${featureSet.version}`,
	}));

	const selectFields: {
		name:
			| 'account_id'
			| 'symbol_id'
			| 'timeframe_id'
			| 'strategy_id'
			| 'feature_set_id';
		label: string;
		options: { value: string; label: string }[];
		description?: string;
	}[] = [
		{ name: 'account_id', label: 'Cuenta', options: accountOptions },
		{
			name: 'symbol_id',
			label: 'Símbolo',
			options: symbolOptions(symbolsQuery.data),
		},
		{
			name: 'timeframe_id',
			label: 'Timeframe',
			options: timeframeOptions(timeframesQuery.data),
		},
		{ name: 'strategy_id', label: 'Estrategia', options: strategyOptions },
		{
			name: 'feature_set_id',
			label: 'Indicadores',
			options: featureSetOptions,
			description: 'Conjunto de indicadores que analiza el agente de IA.',
		},
	];

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-xl">
				<DialogHeader>
					<DialogTitle>Nuevo bot</DialogTitle>
					<DialogDescription>
						El bot aplica una estrategia sobre un símbolo y genera señales que
						pasan las reglas de riesgo.
					</DialogDescription>
				</DialogHeader>
				<form
					id="bot-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							<div className="grid gap-4 sm:grid-cols-2">
								{selectFields.map((item) => (
									<Controller
										key={item.name}
										name={item.name}
										control={form.control}
										render={({ field, fieldState }) => (
											<Field data-invalid={fieldState.invalid}>
												<FieldLabel htmlFor={`bot-${item.name}`} required>
													{item.label}
												</FieldLabel>
												<OptionSelect
													id={`bot-${item.name}`}
													value={field.value}
													onChange={field.onChange}
													options={item.options}
													aria-invalid={fieldState.invalid}
												/>
												{item.description && (
													<FieldDescription>
														{item.description}
													</FieldDescription>
												)}
												{fieldState.invalid && (
													<FieldError errors={[fieldState.error]} />
												)}
											</Field>
										)}
									/>
								))}
								<Controller
									name="mode"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="bot-mode" required>
												Modo
											</FieldLabel>
											<OptionSelect
												id="bot-mode"
												value={field.value}
												onChange={field.onChange}
												options={BOT_MODE_FORM_OPTIONS}
												aria-invalid={fieldState.invalid}
											/>
											{mode === 'live' && (
												<FieldDescription className="text-destructive">
													Las órdenes de este bot usarán dinero real.
												</FieldDescription>
											)}
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							</div>
							<Controller
								name="risk_pct"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field
										data-invalid={fieldState.invalid}
										className="sm:max-w-xs"
									>
										<FieldLabel htmlFor="bot-risk" required>
											Riesgo por operación (%)
										</FieldLabel>
										<Input
											{...field}
											value={String(field.value ?? '')}
											id="bot-risk"
											type="number"
											inputMode="decimal"
											step="0.1"
											min="0.1"
											max={MAX_RISK_PCT}
											placeholder="1"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Máximo 1 % del capital por operación (regla del 1 %).
										</FieldDescription>
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
					<Button
						type="submit"
						form="bot-form"
						disabled={createMutation.isPending}
					>
						{createMutation.isPending && (
							<IconLoader2 className="animate-spin" />
						)}
						Crear bot
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
