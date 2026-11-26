import { createFileRoute } from '@tanstack/react-router';
import { z } from 'zod';

// `?symbol_id=` llega desde "Crear agente" en Explorar mercados.
// `?strategy_id=` llega desde una recomendación de la IA (mismo explorador).
// `?mode=` decide el tipo: `live` (real, por defecto) o `paper` (demo).
const agentNewSearchSchema = z.object({
	symbol_id: z.coerce.number().int().positive().optional().catch(undefined),
	strategy_id: z.coerce.number().int().positive().optional().catch(undefined),
	mode: z.enum(['live', 'paper']).optional().catch(undefined),
});

export const Route = createFileRoute('/_app/agents/new')({
	validateSearch: agentNewSearchSchema,
});
