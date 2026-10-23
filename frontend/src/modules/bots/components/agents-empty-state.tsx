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

/**
 * Bienvenida cuando la persona aún no tiene agentes: qué son y cómo crear el
 * primero. Solo un super admin crea agentes; al socio y al inversor se les
 * dice dónde verlos.
 */
export function AgentsEmptyState() {
	const canManage = useCanManage();
	const isStaff = useHasRole(STAFF_ROLES);

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
						Crea tu primer agente
					</h2>
					<p className="text-muted-foreground">
						Un agente opera por ti sin emociones: aplica una estrategia sobre un
						símbolo y solo propone operaciones que pasan reglas objetivas.
						Puedes empezar con una cuenta de práctica, sin dinero real.
					</p>
					<div>
						<Button render={<Link to="/agents/new" />}>
							<IconPlus />
							Crear agente
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
