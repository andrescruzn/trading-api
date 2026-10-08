import { zodResolver } from '@hookform/resolvers/zod';
import {
	IconChartCandle,
	IconCloudDownload,
	IconLoader2,
} from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import { useFetchCandlesMutation } from '@/modules/market/hooks/use-market-mutations';
import {
	useSymbolsQuery,
	useTimeframesQuery,
} from '@/modules/market/hooks/use-market-queries';
import {
	symbolOptions,
	timeframeOptions,
} from '@/modules/market/lib/market-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { StatCard } from '@/modules/shared/components/stat-card';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { requiredSelectField } from '@/modules/shared/lib/required-select-field';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import {
	Field,
	FieldDescription,
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

const ingestSchema = z.object({
	symbol_id: requiredSelectField('Elige el símbolo'),
	timeframe_id: requiredSelectField('Elige el timeframe'),
	limit: z.coerce
		.number({ message: 'Escribe un número' })
		.int('Debe ser un número entero')
		.min(1, 'Mínimo 1 vela')
		.max(1000, 'Máximo 1000 velas por descarga'),
});

export function AdminCandlesIngestPage() {
	usePageBreadcrumb([
		{ label: 'Administración' },
		{ label: 'Descargar velas' },
	]);
	const symbolsQuery = useSymbolsQuery({ is_active: true });
	const timeframesQuery = useTimeframesQuery();
	const fetchMutation = useFetchCandlesMutation();

	const form = useForm<
		z.input<typeof ingestSchema>,
		unknown,
		z.output<typeof ingestSchema>
	>({
		resolver: zodResolver(ingestSchema),
		defaultValues: { symbol_id: null, timeframe_id: null, limit: 500 },
	});

	function handleSubmit(values: z.output<typeof ingestSchema>) {
		fetchMutation.mutate(
			{
				symbol_id: Number(values.symbol_id),
				timeframe_id: Number(values.timeframe_id),
				limit: values.limit,
			},
			{
				onError: (error) =>
					toast.add({
						title: 'No pudimos descargar las velas',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	const result = fetchMutation.data;
	const resultSymbolId = fetchMutation.variables?.symbol_id;
	const resultTimeframeId = fetchMutation.variables?.timeframe_id;

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Descargar velas"
				description="Trae velas OHLCV del exchange real y las guarda. Si ya existían, se actualizan."
			/>
			<Card className="max-w-2xl">
				<CardHeader>
					<CardTitle>Parámetros</CardTitle>
					<CardDescription>
						El exchange se toma del símbolo. La descarga puede tardar unos
						segundos.
					</CardDescription>
				</CardHeader>
				<CardContent>
					<form onSubmit={form.handleSubmit(handleSubmit)} noValidate>
						<FieldGroup>
							<div className="grid gap-4 sm:grid-cols-2">
								<Controller
									name="symbol_id"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="ingest-symbol" required>
												Símbolo
											</FieldLabel>
											<OptionSelect
												id="ingest-symbol"
												value={field.value}
												onChange={field.onChange}
												options={symbolOptions(symbolsQuery.data)}
												aria-invalid={fieldState.invalid}
											/>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)}
								/>
								<Controller
									name="timeframe_id"
									control={form.control}
									render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="ingest-timeframe" required>
												Timeframe
											</FieldLabel>
											<OptionSelect
												id="ingest-timeframe"
												value={field.value}
												onChange={field.onChange}
												options={timeframeOptions(timeframesQuery.data)}
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
								name="limit"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field
										data-invalid={fieldState.invalid}
										className="sm:max-w-xs"
									>
										<FieldLabel htmlFor="ingest-limit" required>
											Cantidad de velas
										</FieldLabel>
										<Input
											{...field}
											value={String(field.value ?? '')}
											id="ingest-limit"
											type="number"
											inputMode="numeric"
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Entre 1 y 1000, las más recientes.
										</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Field orientation="horizontal" className="justify-end">
								<Button type="submit" disabled={fetchMutation.isPending}>
									{fetchMutation.isPending ? (
										<IconLoader2 className="animate-spin" />
									) : (
										<IconCloudDownload />
									)}
									Descargar del exchange
								</Button>
							</Field>
						</FieldGroup>
					</form>
				</CardContent>
			</Card>

			{result && (
				<div className="flex flex-col gap-4">
					<div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
						<StatCard label="Exchange" value={result.exchange} />
						<StatCard label="Símbolo" value={result.symbol} />
						<StatCard label="Timeframe" value={result.timeframe} />
						<StatCard
							label="Velas guardadas"
							value={result.rows_fetched.toLocaleString('es-CO')}
						/>
					</div>
					<div>
						<Button
							variant="outline"
							render={
								<Link
									to="/market/candles"
									search={{
										symbol_id: resultSymbolId,
										timeframe_id: resultTimeframeId,
									}}
								/>
							}
						>
							<IconChartCandle />
							Ver velas
						</Button>
					</div>
				</div>
			)}
		</div>
	);
}
