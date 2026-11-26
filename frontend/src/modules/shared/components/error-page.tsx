import { IconAlertTriangle, IconRefresh } from '@tabler/icons-react';
import { type ErrorComponentProps, Link } from '@tanstack/react-router';
import { Button } from '@/modules/ui/components/button';

export function ErrorPage({ error, reset }: ErrorComponentProps) {
	const isDev = import.meta.env.DEV;

	return (
		<div className="flex min-h-svh flex-col items-center justify-center gap-6 p-6 text-center">
			<div className="flex size-16 items-center justify-center rounded-full bg-destructive/10">
				<IconAlertTriangle className="size-8 text-destructive" />
			</div>
			<div className="flex flex-col items-center gap-1">
				<h1 className="text-2xl font-bold">Algo salió mal</h1>
				<p className="max-w-sm text-sm text-balance text-muted-foreground">
					Algo salió mal de nuestra parte. Inténtalo de nuevo en unos minutos.
					Si sigue pasando, avísale al equipo de soporte.
				</p>
			</div>

			{isDev && (
				<div className="w-full max-w-2xl overflow-auto rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-left">
					<p className="font-mono text-sm font-semibold text-destructive">
						{error.name}: {error.message}
					</p>
					{error.stack && (
						<pre className="mt-2 font-mono text-xs whitespace-pre-wrap text-muted-foreground">
							{error.stack}
						</pre>
					)}
				</div>
			)}

			<div className="flex gap-3">
				<Button variant="outline" onClick={reset}>
					<IconRefresh />
					Reintentar
				</Button>
				<Button render={<Link to="/" />}>Volver al inicio</Button>
			</div>
		</div>
	);
}
