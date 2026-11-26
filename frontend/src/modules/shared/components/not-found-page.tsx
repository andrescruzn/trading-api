import { IconSearch } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { Button } from '@/modules/ui/components/button';

export function NotFoundPage() {
	return (
		<div className="flex min-h-svh flex-col items-center justify-center gap-6 p-6 text-center">
			<div className="flex size-16 items-center justify-center rounded-full bg-muted">
				<IconSearch className="size-8 text-muted-foreground" />
			</div>
			<div className="flex flex-col items-center gap-1">
				<h1 className="text-2xl font-bold">No encontramos esta página</h1>
				<p className="max-w-sm text-sm text-balance text-muted-foreground">
					Puede que se haya movido o que el enlace no sea correcto.
				</p>
			</div>
			<Button render={<Link to="/" />}>Volver al inicio</Button>
		</div>
	);
}
