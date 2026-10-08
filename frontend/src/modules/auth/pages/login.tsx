import {
	IconChartCandle,
	IconRobot,
	IconScale,
	IconShieldCheck,
	IconTargetArrow,
} from '@tabler/icons-react';
import { LoginForm } from '../components/login-form';
import { SessionExpiredDialog } from '../components/session-expired-dialog';

const FEATURES = [
	{
		icon: IconScale,
		title: 'Filtro de régimen',
		text: 'Solo opera en el mercado para el que se diseñó cada estrategia.',
	},
	{
		icon: IconShieldCheck,
		title: 'Regla del 1 %',
		text: 'Nunca arriesga más del 1 % del capital por operación.',
	},
	{
		icon: IconTargetArrow,
		title: 'Riesgo/beneficio 2:1',
		text: 'Si la operación no paga al menos el doble de lo que arriesga, se descarta.',
	},
	{
		icon: IconRobot,
		title: 'Agente de IA',
		text: 'Evalúa cada señal contra las reglas, sin emociones.',
	},
];

export function LoginPage() {
	return (
		<>
			<SessionExpiredDialog />
			<div className="grid min-h-svh lg:grid-cols-2">
				<div className="relative hidden flex-col justify-between overflow-hidden bg-primary p-10 text-primary-foreground lg:flex">
					<div className="flex items-center gap-2 font-semibold">
						<div className="flex size-9 items-center justify-center rounded-lg bg-primary-foreground/15">
							<IconChartCandle className="size-5" />
						</div>
						Trading App
					</div>
					<div className="flex max-w-md flex-col gap-8">
						<div className="flex flex-col gap-2">
							<h2 className="text-3xl font-semibold">Opera con reglas, no con emociones</h2>
							<p className="text-primary-foreground/80">
								El sistema solo propone operaciones que pasan reglas objetivas.
							</p>
						</div>
						<ul className="flex flex-col gap-5">
							{FEATURES.map((feature) => (
								<li key={feature.title} className="flex gap-3">
									<feature.icon className="mt-0.5 size-5 shrink-0" />
									<div>
										<p className="font-medium">{feature.title}</p>
										<p className="text-sm text-primary-foreground/75">
											{feature.text}
										</p>
									</div>
								</li>
							))}
						</ul>
					</div>
					<p className="text-xs text-primary-foreground/60">
						Sistema privado · solo usuarios autorizados
					</p>
				</div>
				<div className="relative flex flex-col gap-4 p-6 md:p-10">
					<div className="flex justify-center gap-2 lg:hidden">
						<div className="flex items-center gap-2 font-semibold">
							<div className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
								<IconChartCandle className="size-5" />
							</div>
							Trading App
						</div>
					</div>
					<div className="flex flex-1 items-center justify-center">
						<div className="w-full max-w-md rounded-xl border bg-card px-6 pt-8 pb-12 shadow-sm lg:max-w-sm lg:border-none lg:bg-transparent lg:p-0 lg:shadow-none">
							<LoginForm />
						</div>
					</div>
				</div>
			</div>
		</>
	);
}
