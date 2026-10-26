import {
	IconChartCandle,
	IconPlus,
	IconRobot,
	IconShieldCheck,
	IconSparkles,
} from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { useCanManage } from '@/modules/auth/hooks/use-can-manage';
import { useHasRole } from '@/modules/auth/hooks/use-has-role';
import { STAFF_ROLES } from '@/modules/auth/lib/roles';
import type { BotMode } from '@/modules/bots/api/bots.api';
import { Button } from '@/modules/ui/components/button';

const HOW_IT_WORKS = [
	{
		icon: IconChartCandle,
		title: 'Vigila un símbolo',
		text: 'Descarga sus velas y calcula indicadores como RSI, medias móviles o MACD.',
	},
	{
		icon: IconSparkles,
		title: 'Aplica tu estrategia',
		text: 'Si se cumplen sus reglas y el régimen del mercado, la IA evalúa la operación.',
	},
	{
		icon: IconShieldCheck,
		title: 'Respeta tu riesgo',
		text: 'Solo propone operaciones con riesgo de máximo 1 % y riesgo/beneficio de 2:1 o más.',
	},
];

/** Lo que cambia entre la bienvenida de agentes reales y la de agentes demo. */
const COPY: Record<BotMode, { title: string; text: string; cta: string }> = {
	live: {
		title: 'Crea tu primer agente real',
		text: 'Un agente opera por ti sin emociones: aplica una estrategia sobre un símbolo y solo propone operaciones que pasan reglas objetivas. Los agentes reales operan con la billetera de Binance y con el dinero que les asignes desde el fondo.',
		cta: 'Crear agente real',
	},
	paper: {
		title: 'Crea tu primer agente demo',
		text: 'Un agente demo hace lo mismo que uno real, pero con dinero simulado: escribes cuánto quieres invertir y ves cómo le iría a la estrategia, sin tocar la billetera ni el fondo.',
		cta: 'Crear agente demo',
	},
};

/**
 * Bienvenida cuando aún no hay agentes de un tipo: qué son y cómo crear el
 * primero. Solo un super admin crea agentes; al socio y al inversor se les
 * dice dónde verlos.
 */
export function AgentsEmptyState({ mode }: { mode: BotMode }) {
	const canManage = useCanManage();
	const isStaff = useHasRole(STAFF_ROLES);
	const copy = COPY[mode];

	if (!canManage && mode === 'paper') {
		return (
			<p className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
				Aún no hay agentes demo.
			</p>
		);
	}

	if (!canManage) {
		return (
			<div className="flex flex-col items-start gap-3 rounded-2xl border bg-card p-6">
				<h2 className="text-lg font-semibold tracking-tight">
					Los agentes los crean los super admin
				</h2>
				<p className="text-sm text-muted-foreground">
					{isStaff
						? 'Como socio puedes revisar los agentes del fondo, sus señales y sus órdenes, sin hacer cambios.'
						: 'Aquí verás el estado de los agentes en los que participa tu dinero.'}
				</p>
				{isStaff && (
					<Button variant="outline" render={<Link to="/admin/fund-agents" />}>
						<IconRobot />
						Ver los agentes del fondo
					</Button>
				)}
			</div>
		);
	}

	return (
		<div className="relative overflow-hidden rounded-2xl border bg-card p-6 sm:p-10">
			<div
				aria-hidden
				className="pointer-events-none absolute -top-24 -right-24 size-72 rounded-full bg-primary/10 blur-3xl"
			/>
			<div className="relative flex flex-col gap-8">
				<div className="flex max-w-xl flex-col gap-3">
					<span className="flex size-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
						<IconRobot className="size-6" />
					</span>
					<h2 className="text-2xl font-semibold tracking-tight">
						{copy.title}
					</h2>
					<p className="text-muted-foreground">{copy.text}</p>
					<div>
						<Button render={<Link to="/agents/new" search={{ mode }} />}>
							<IconPlus />
							{copy.cta}
						</Button>
					</div>
				</div>
				<ol className="grid gap-4 sm:grid-cols-3">
					{HOW_IT_WORKS.map((item, index) => (
						<li
							key={item.title}
							className="flex animate-in flex-col gap-2 rounded-xl border bg-background/60 p-4 fade-in slide-in-from-bottom-2 fill-mode-both"
							style={{ animationDelay: `${index * 80}ms` }}
						>
							<span className="flex items-center gap-2 text-sm font-medium">
								<item.icon className="size-4 text-primary" />
								{item.title}
							</span>
							<span className="text-sm text-muted-foreground">{item.text}</span>
						</li>
					))}
				</ol>
			</div>
		</div>
	);
}
