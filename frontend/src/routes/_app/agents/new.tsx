import { createFileRoute } from '@tanstack/react-router';
import { z } from 'zod';

// `?symbol_id=` llega desde "Crear agente" en Explorar mercados.
const agentNewSearchSchema = z.object({
	symbol_id: z.coerce.number().int().positive().optional().catch(undefined),
});

export const Route = createFileRoute('/_app/agents/new')({
	validateSearch: agentNewSearchSchema,
});
