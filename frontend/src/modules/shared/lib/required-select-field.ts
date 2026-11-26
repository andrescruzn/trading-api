import { z } from 'zod';

/**
 * `Select` (base-ui) representa "sin selección" como `null`, no como `''` —
 * y además resetea a `null` un valor controlado que ya no aparece en `items`
 * (ej. al cambiar de departamento y recargar las ciudades). Si se validara
 * con `z.string().min(1, ...)` a secas, Zod rechaza el `null` por tipo antes
 * de llegar al mensaje personalizado ("Invalid input: expected string,
 * received null"). `.nullable()` (no `.nullish()`: no queremos que Zod marque
 * la propiedad como opcional en el objeto, rompería el tipado de
 * `handleSubmit`) + `.refine` con predicado de tipo acepta `null` como
 * entrada y angosta la salida a `string`.
 */
function requiredSelectField(message: string) {
	return z
		.string()
		.nullable()
		.refine((value): value is string => !!value, { message });
}

export { requiredSelectField };
