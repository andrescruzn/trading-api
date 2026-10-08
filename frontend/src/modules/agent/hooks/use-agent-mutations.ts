import { useMutation } from '@tanstack/react-query';
import { type AnalyzeInput, analyze } from '@/modules/agent/api/agent.api';

/**
 * El análisis no cambia datos que estén en caché (no crea señales ni órdenes):
 * es una mutación solo porque es un POST costoso que se lanza a demanda.
 */
function useAnalyzeMutation() {
	return useMutation({
		mutationFn: (input: AnalyzeInput) => analyze(input),
	});
}

export { useAnalyzeMutation };
