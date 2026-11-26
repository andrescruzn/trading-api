import { IconHandClick, IconRobot, IconUserCheck } from '@tabler/icons-react';
import type { ReactNode } from 'react';
import type { BotExecutionMode, BotMode } from '@/modules/bots/api/bots.api';
import { ChoiceCard } from '@/modules/bots/components/agent-wizard/choice-card';
import {
	EXECUTION_MODE_DESCRIPTIONS,
	EXECUTION_MODE_LABELS,
} from '@/modules/bots/lib/bots-labels';

const MODE_ICONS: Record<BotExecutionMode, ReactNode> = {
	manual: <IconHandClick className="size-4" />,
	approval: <IconUserCheck className="size-4" />,
	auto: <IconRobot className="size-4" />,
};

const MODES: BotExecutionMode[] = ['manual', 'approval', 'auto'];

type ExecutionModePickerProps = {
	value: BotExecutionMode;
	onChange: (mode: BotExecutionMode) => void;
	/** Modo de la cuenta: en live, Automático lleva un aviso. */
	accountMode?: BotMode;
	disabled?: boolean;
};

/** Qué hace el agente cuando la IA aprueba una operación. */
export function ExecutionModePicker({
	value,
	onChange,
	accountMode,
	disabled,
}: ExecutionModePickerProps) {
	return (
		<div className="grid gap-3 sm:grid-cols-3">
			{MODES.map((mode) => (
				<ChoiceCard
					key={mode}
					selected={value === mode}
					onSelect={() => onChange(mode)}
					disabled={disabled}
					eyebrow={
						<span className="inline-flex items-center gap-1.5">
							{MODE_ICONS[mode]}
							{mode === 'manual' ? 'Tú decides todo' : 'Cada vela cerrada'}
						</span>
					}
					title={EXECUTION_MODE_LABELS[mode]}
					description={EXECUTION_MODE_DESCRIPTIONS[mode]}
					footer={
						mode === 'auto' && accountMode === 'live' ? (
							<span className="text-xs text-destructive">
								Envía órdenes con dinero real sin pedirte confirmación.
							</span>
						) : undefined
					}
				/>
			))}
		</div>
	);
}
