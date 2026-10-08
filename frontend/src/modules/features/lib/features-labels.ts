import type { FeatureSet } from '@/modules/features/api/features.api';
import type { SelectOption } from '@/modules/shared/components/option-select';

/** `default · v1.0.0`. */
function featureSetLabel(
	featureSet: Pick<FeatureSet, 'name' | 'version'>,
): string {
	return `${featureSet.name} · v${featureSet.version}`;
}

function featureSetOptions(
	featureSets: FeatureSet[] | undefined,
): SelectOption[] {
	return (featureSets ?? []).map((featureSet) => ({
		value: String(featureSet.id),
		label: featureSetLabel(featureSet),
	}));
}

/**
 * Valida que el texto sea un objeto JSON (no arreglo ni valor suelto), como
 * exige `spec: dict` en el backend. Devuelve el mensaje de error o `null`.
 */
function jsonObjectError(value: string): string | null {
	try {
		const parsed: unknown = JSON.parse(value);
		if (
			typeof parsed !== 'object' ||
			parsed === null ||
			Array.isArray(parsed)
		) {
			return 'Debe ser un objeto JSON, entre llaves { }';
		}
		return null;
	} catch {
		return 'El JSON no es válido. Revisa comillas, comas y llaves';
	}
}

export { featureSetLabel, featureSetOptions, jsonObjectError };
