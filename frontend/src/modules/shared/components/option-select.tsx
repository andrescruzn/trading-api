import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from '@/modules/ui/components/select';
import { cn } from '@/modules/ui/lib/utils';

type SelectOption = { value: string; label: string };

type OptionSelectProps = {
	id?: string;
	/** `null` = sin selección (así lo representa Base UI). */
	value: string | null;
	onChange: (value: string | null) => void;
	options: SelectOption[];
	placeholder?: string;
	disabled?: boolean;
	'aria-invalid'?: boolean;
	/** Para filtros sin `FieldLabel` visible. */
	'aria-label'?: string;
	size?: 'sm' | 'default';
	className?: string;
};

/**
 * `Select` de Base UI con la lista de opciones como datos. Úsalo para filtros
 * y campos de formulario simples (con `Controller`, ver
 * `requiredSelectField` para validar el `null`). Los IDs numéricos del
 * backend viajan como string: conviértelos con `Number()` al enviar.
 */
export function OptionSelect({
	id,
	value,
	onChange,
	options,
	placeholder = 'Selecciona una opción',
	disabled,
	size = 'default',
	className,
	...props
}: OptionSelectProps) {
	return (
		<Select
			value={value}
			onValueChange={(next) => onChange((next as string | null) ?? null)}
			items={options}
			disabled={disabled}
		>
			<SelectTrigger
				id={id}
				size={size}
				className={cn('w-full', className)}
				aria-invalid={props['aria-invalid']}
				aria-label={props['aria-label']}
			>
				<SelectValue placeholder={placeholder} />
			</SelectTrigger>
			<SelectContent alignItemWithTrigger={false}>
				{options.map((option) => (
					<SelectItem key={option.value} value={option.value}>
						{option.label}
					</SelectItem>
				))}
			</SelectContent>
		</Select>
	);
}

export type { SelectOption };
