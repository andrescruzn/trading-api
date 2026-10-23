import { z } from 'zod';

/**
 * Monto en texto mayor que 0: viaja como string para no perder precisión
 * (el backend lo guarda como DECIMAL). Acepta coma decimal.
 */
const positiveAmountField = z
	.string()
	.trim()
	.min(1, 'Escribe el monto')
	.transform((value) => value.replace(',', '.'))
	.refine(
		(value) => Number.isFinite(Number(value)) && Number(value) > 0,
		'Debe ser un número mayor que 0',
	);

/** Texto obligatorio con límite (notas y motivos). */
function requiredText(message: string, max = 500, min = 1) {
	return z
		.string()
		.trim()
		.min(min, message)
		.max(max, `Máximo ${max} caracteres`);
}

export { positiveAmountField, requiredText };
