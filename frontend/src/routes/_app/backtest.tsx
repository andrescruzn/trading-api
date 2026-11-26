import { createFileRoute } from '@tanstack/react-router';
import { z } from 'zod';

// `?strategy_id=` llega desde "Probar en el pasado" en Estrategias.
const backtestSearchSchema = z.object({
	strategy_id: z.coerce.number().int().positive().optional().catch(undefined),
});

export const Route = createFileRoute('/_app/backtest')({
	validateSearch: backtestSearchSchema,
});
