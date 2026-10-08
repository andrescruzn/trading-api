import { zodResolver } from '@hookform/resolvers/zod';
import { IconCpu, IconLoader2 } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { useCalculateFeaturesMutation } from '@/modules/features/hooks/use-features-mutations';
import { useFeatureSetsQuery } from '@/modules/features/hooks/use-features-queries';
import { featureSetOptions } from '@/modules/features/lib/features-labels';
import {
	useSymbolsQuery,
	useTimeframesQuery,
} from '@/modules/market/hooks/use-market-queries';
import { symbolOptions, timeframeOptions } from '@/modules/market/lib/market-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { formatNumber } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
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
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { toast } from '@/modules/ui/components/toast';

const calculateSchema = z.object({
	symbol_id: requiredSelectField('Elige el símbolo'),
	timeframe_id: requiredSelectField('Elige el timeframe'),
	feature_set_id: requiredSelectField('Elige el feature set'),
});

type CalculateValues = z.infer<typeof calculateSchema>;

const EMPTY_VALUES: CalculateValues = {
	symbol_id: null,
	timeframe_id: null,
	feature_set_id: null,
};

type CalculateFeaturesDialogProps = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
};

export function CalculateFeaturesDialog({
	open,
	onOpenChange,
}: CalculateFeaturesDialogProps) {
	const symbolsQuery = useSymbolsQuery({ is_active: true });
	const timeframesQuery = useTimeframesQuery();
	const featureSetsQuery = useFeatureSetsQuery();
	const calculateMutation = useCalculateFeaturesMutation();

	const form = useForm<CalculateValues>({
		resolver: zodResolver(calculateSchema),
		defaultValues: EMPTY_VALUES,
	});

	useEffect(() => {
		if (open) form.reset(EMPTY_VALUES);
	}, [open, form]);

	function handleSubmit(values: CalculateValues) {
		calculateMutation.mutate(
			{
				symbol_id: Number(values.symbol_id),
				timeframe_id: Number(values.timeframe_id),
				feature_set_id: Number(values.feature_set_id),
			},
			{
				onSuccess: (result) => {
					toast.add({
						title: 'Indicadores calculados',
						description: `Se calcularon los indicadores de ${formatNumber(result.rows_calculated, 0)} velas (${formatNumber(result.rows_affected, 0)} filas guardadas o actualizadas).`,
						type: 'success',
					});
					onOpenChange(false);
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos calcular los indicadores',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	const selects: {
		name: keyof CalculateValues;
		label: string;
		options: { value: string; label: string }[];
	}[] = [
		{ name: 'symbol_id', label: 'Símbolo', options: symbolOptions(symbolsQuery.data) },
		{
			name: 'timeframe_id',
			label: 'Timeframe',
			options: timeframeOptions(timeframesQuery.data),
		},
		{
			name: 'feature_set_id',
			label: 'Feature set',
			options: featureSetOptions(featureSetsQuery.data),
		},
	];

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Calcular indicadores</DialogTitle>
					<DialogDescription>
						Calcula RSI, EMA, MACD, ATR, bandas de Bollinger y régimen sobre las
						velas guardadas. Necesita al menos 220 velas y puede tardar unos
						segundos.
					</DialogDescription>
				</DialogHeader>
				<form
					id="calculate-features-form"
					onSubmit={form.handleSubmit(handleSubmit)}
					noValidate
					className="contents"
				>
					<DialogBody>
						<FieldGroup>
							{selects.map((item) => (
								<Controller
									key={item.name}
									name={item.name}
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor={`calculate-${item.name}`} required>
												{item.label}
											</FieldLabel>
											<OptionSelect
												id={`calculate-${item.name}`}
												value={field.value}
												onChange={field.onChange}
												options={item.options}
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
							))}
						</FieldGroup>
					</DialogBody>
				</form>
				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancelar
					</Button>
					<Button
						type="submit"
						form="calculate-features-form"
						disabled={calculateMutation.isPending}
					>
						{calculateMutation.isPending ? (
							<IconLoader2 className="animate-spin" />
						) : (
							<IconCpu />
						)}
						{calculateMutation.isPending ? 'Calculando…' : 'Calcular'}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
