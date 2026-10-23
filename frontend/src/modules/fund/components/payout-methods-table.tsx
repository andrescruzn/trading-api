import { IconLoader2, IconTrash } from '@tabler/icons-react';
import { useState } from 'react';
import type { PayoutMethod } from '@/modules/fund/api/fund-payouts.api';
import { useDeactivatePayoutMethodMutation } from '@/modules/fund/hooks/use-fund-payouts-mutations';
import { PAYOUT_KIND_LABELS } from '@/modules/fund/lib/fund-payouts-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { formatDateTime, toTimestamp } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from '@/modules/ui/components/alert-dialog';
import { Badge } from '@/modules/ui/components/badge';
import { Button } from '@/modules/ui/components/button';
import { toast } from '@/modules/ui/components/toast';

type PayoutMethodsTableProps = {
	rows: PayoutMethod[] | undefined;
	isLoading: boolean;
	error: unknown;
};

/** Mis medios de pago: resumen enmascarado y desde cuándo se pueden usar. */
export function PayoutMethodsTable({
	rows,
	isLoading,
	error,
}: PayoutMethodsTableProps) {
	const mutation = useDeactivatePayoutMethodMutation();
	const [removing, setRemoving] = useState<PayoutMethod | null>(null);
	const now = Date.now();

	function remove() {
		if (!removing) return;
		mutation.mutate(removing.id, {
			onSuccess: () => {
				toast.add({ title: 'Medio de pago quitado', type: 'success' });
				setRemoving(null);
			},
			onError: (err) =>
				toast.add({
					title: 'No pudimos quitar el medio de pago',
					description: getErrorMessage(err),
					type: 'error',
				}),
		});
	}

	const columns: DataTableColumn<PayoutMethod>[] = [
		{
			id: 'label',
			header: 'Medio',
			cell: (row) => (
				<div className="flex flex-col">
					<span className="font-medium">{row.label}</span>
					<span className="text-xs text-muted-foreground">
						{PAYOUT_KIND_LABELS[row.kind]} · {row.masked}
					</span>
				</div>
			),
		},
		{
			id: 'usable',
			header: 'Estado',
			cell: (row) =>
				(toTimestamp(row.usable_from) ?? 0) <= now ? (
					<Badge>Listo</Badge>
				) : (
					<Badge variant="secondary">
						Se puede usar desde el {formatDateTime(row.usable_from)}
					</Badge>
				),
		},
		{
			id: 'actions',
			header: <span className="sr-only">Acciones</span>,
			className: 'text-right',
			cell: (row) => (
				<Button variant="ghost" size="sm" onClick={() => setRemoving(row)}>
					<IconTrash />
					Quitar
				</Button>
			),
		},
	];

	return (
		<>
			<DataTable
				columns={columns}
				rows={rows}
				getRowId={(row) => row.id}
				isLoading={isLoading}
				error={error}
				errorTitle="No pudimos cargar tus medios de pago"
				empty="Aún no registras a dónde te pagamos. Agrega una cuenta bancaria o Nequi."
			/>
			<AlertDialog
				open={!!removing}
				onOpenChange={(open) => !open && setRemoving(null)}
			>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>¿Quitar «{removing?.label}»?</AlertDialogTitle>
						<AlertDialogDescription>
							Ya no podrás pedir retiros a este medio. Los retiros por pagar que
							lo usan se pagan igual.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel>Volver</AlertDialogCancel>
						<AlertDialogAction
							variant="destructive"
							disabled={mutation.isPending}
							onClick={remove}
						>
							{mutation.isPending && <IconLoader2 className="animate-spin" />}
							Quitar medio
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</>
	);
}
