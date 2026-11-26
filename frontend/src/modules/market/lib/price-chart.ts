/** Línea de referencia en el gráfico de precio (entrada, stop loss, take profit…). */
type PriceLevel = {
	label: string;
	value: number;
	/** Solo la línea lleva el color; el texto va en tokens de texto. */
	tone: 'neutral' | 'good' | 'critical';
};

export type { PriceLevel };
