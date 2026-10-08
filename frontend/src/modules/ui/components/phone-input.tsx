import type * as React from 'react';
import { Input } from '@/modules/ui/components/input';

const PHONE_DIGITS_LENGTH = 10;

const PHONE_NUMBER_PATTERN = /^\d{3} \d{3} \d{4}$/;

const PHONE_PLACEHOLDER = 'Ej. 300 123 4567';

function formatPhoneNumber(rawValue: string): string {
	const digits = rawValue.replace(/\D/g, '').slice(0, PHONE_DIGITS_LENGTH);
	return [digits.slice(0, 3), digits.slice(3, 6), digits.slice(6, 10)]
		.filter(Boolean)
		.join(' ');
}

function toPhoneDigits(value: string): string {
	return value.replace(/\D/g, '').slice(0, PHONE_DIGITS_LENGTH);
}

type PhoneInputProps = Omit<
	React.ComponentProps<typeof Input>,
	'type' | 'onChange' | 'value'
> & {
	value?: string;
	onChange?: (value: string) => void;
};

function PhoneInput({
	value,
	onChange,
	placeholder,
	...props
}: PhoneInputProps) {
	return (
		<Input
			{...props}
			type="tel"
			inputMode="numeric"
			placeholder={placeholder ?? PHONE_PLACEHOLDER}
			value={value}
			onChange={(event) => onChange?.(formatPhoneNumber(event.target.value))}
		/>
	);
}

export {
	formatPhoneNumber,
	PHONE_DIGITS_LENGTH,
	PHONE_NUMBER_PATTERN,
	PHONE_PLACEHOLDER,
	PhoneInput,
	toPhoneDigits,
};
