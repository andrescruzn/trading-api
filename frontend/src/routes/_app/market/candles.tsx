import { createFileRoute } from '@tanstack/react-router';
import { z } from 'zod';

// `?symbol_id=` llega desde "Ver velas" en Símbolos o en Descargar velas.
const candlesSearchSchema = z.object({
	symbol_id: z.coerce.number().int().positive().optional().catch(undefined),
	timeframe_id: z.coerce.number().int().positive().optional().catch(undefined),
});

export const Route = createFileRoute('/_app/market/candles')({
	validateSearch: candlesSearchSchema,
});
