import {
	INDICATOR_GROUP_HINTS,
	INDICATOR_GROUP_LABELS,
} from '@/modules/features/lib/features-labels';

/** Explicación plegable de cada indicador y del régimen. */
export function IndicatorsGlossary() {
	return (
		<details className="group rounded-xl border bg-card px-4 py-3 text-sm">
			<summary className="cursor-pointer font-medium marker:text-muted-foreground">
				¿Qué mide cada indicador?
			</summary>
			<dl className="mt-3 grid gap-3 sm:grid-cols-2">
				{Object.entries(INDICATOR_GROUP_HINTS).map(([group, hint]) => (
					<div key={group} className="flex flex-col gap-0.5">
						<dt className="font-medium">
							{
								INDICATOR_GROUP_LABELS[
									group as keyof typeof INDICATOR_GROUP_LABELS
								]
							}
						</dt>
						<dd className="text-muted-foreground">{hint}</dd>
					</div>
				))}
				<div className="flex flex-col gap-0.5">
					<dt className="font-medium">Régimen</dt>
					<dd className="text-muted-foreground">
						Si el mercado va en tendencia alcista, bajista o de lado. Cada
						estrategia solo opera en el régimen que declara.
					</dd>
				</div>
			</dl>
		</details>
	);
}
