import { IconAlertTriangle, IconFlask, IconWallet } from '@tabler/icons-react';
import type { ReactNode } from 'react';
import type { BotMode } from '@/modules/bots/api/bots.api';
import { formatNumber } from '@/modules/shared/lib/format';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import {
	Field,
	FieldDescription,
	FieldError,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';

type MoneyStepProps = {
	/** `live` = agente real · `paper` = agente demo. */
	mode: BotMode;
	/** Moneda de cotización del símbolo elegido. */
	currency: string;
	/** El símbolo es un perpetuo: en real opera en la billetera de Futuros. */
	perpetual?: boolean;
	/** Solo demo: monto escrito (texto del input). */
	capital?: string;
	onCapitalChange?: (value: string) => void;
	capitalError?: string;
};

function Explainer({
	icon,
	title,
	children,
}: {
	icon: ReactNode;
	title: string;
	children: ReactNode;
}) {
	return (
		<div className="flex gap-3 rounded-xl border bg-muted/30 p-4">
			<span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
				{icon}
			</span>
			<div className="flex flex-col gap-1">
				<p className="font-medium">{title}</p>
				<p className="text-sm text-muted-foreground">{children}</p>
			</div>
		</div>
	);
}

/**
 * Paso 3: con qué dinero opera el agente. Un agente real usa la billetera de
 * Binance (la única de la plataforma) con lo que se le asigne desde el fondo;
 * uno demo, el monto simulado que se escribe aquí.
 */
export function MoneyStep({
	mode,
	currency,
	perpetual = false,
	capital = '',
	onCapitalChange,
	capitalError,
}: MoneyStepProps) {
	if (mode === 'live') {
		return (
			<div className="flex flex-col gap-4">
				<Explainer
					icon={<IconWallet className="size-5" />}
					title="Billetera de Binance"
				>
					Opera con la billetera de Binance de la plataforma. Su capital es el
					dinero que le asignes desde Administración → Fondo → Agentes del
					fondo: sin asignación no genera señales.
				</Explainer>
				<Alert variant="destructive">
					<IconAlertTriangle />
					<AlertTitle>Este agente usa dinero real</AlertTitle>
					<AlertDescription>
						Sus órdenes se envían a Binance. Si quieres probar la estrategia
						primero, crea un agente demo.
						{perpetual &&
							' Este símbolo es un perpetuo: opera en la billetera de Futuros de Binance, sin apalancamiento (1x) y solo comprando. Pasa USDT de Spot a Futuros antes de iniciarlo.'}
					</AlertDescription>
				</Alert>
			</div>
		);
	}

	const capitalNumber = Number(capital);
	return (
		<div className="flex flex-col gap-4">
			<Explainer
				icon={<IconFlask className="size-5" />}
				title="Dinero simulado"
			>
				El agente demo no toca la billetera ni el fondo: opera con el monto que
				escribas y ves cómo le iría a la estrategia.
			</Explainer>
			<Field data-invalid={!!capitalError}>
				<FieldLabel htmlFor="agent-demo-capital" required>
					Monto a invertir ({currency})
				</FieldLabel>
				<Input
					id="agent-demo-capital"
					type="number"
					inputMode="decimal"
					min="1"
					value={capital}
					aria-invalid={!!capitalError}
					onChange={(event) => onCapitalChange?.(event.target.value)}
					className="sm:max-w-xs"
				/>
				<FieldDescription>
					Con la regla del 1 %, cada operación arriesga como máximo{' '}
					{capitalNumber > 0
						? `${formatNumber(capitalNumber * 0.01)} ${currency}`
						: '—'}
					.
				</FieldDescription>
				{capitalError && <FieldError errors={[{ message: capitalError }]} />}
			</Field>
		</div>
	);
}
