import { IconPlus, IconSearch } from '@tabler/icons-react';
import { useState } from 'react';
import type { Account, AccountBalance } from '@/modules/accounts/api/accounts.api';
import { AccountModeBadge } from '@/modules/accounts/components/account-badges';
import { RecordBalanceDialog } from '@/modules/accounts/components/record-balance-dialog';
import { useAccountBalancesQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { useDebouncedValue } from '@/modules/shared/hooks/use-debounced-value';
import { formatDateTime, formatNumber } from '@/modules/shared/lib/format';
import { Button } from '@/modules/ui/components/button';
import { Input } from '@/modules/ui/components/input';
import {
	Sheet,
	SheetContent,
	SheetDescription,
	SheetHeader,
	SheetTitle,
} from '@/modules/ui/components/sheet';

const columns: DataTableColumn<AccountBalance>[] = [
	{
		id: 'asset',
		header: 'Activo',
		cell: (row) => <span className="font-mono font-medium">{row.asset}</span>,
	},
	...(['free', 'locked', 'total'] as const).map(
		(key): DataTableColumn<AccountBalance> => ({
			id: key,
			header: { free: 'Libre', locked: 'Bloqueado', total: 'Total' }[key],
			className: 'text-right font-mono tabular-nums',
			cell: (row) => formatNumber(row[key]),
		}),
	),
	{
		id: 'ts',
		header: 'Fecha',
		cell: (row) => formatDateTime(row.ts),
		skeletonClassName: 'w-32',
	},
];

type AccountBalancesSheetProps = {
	/** `null` = cerrado. */
	account: Account | null;
	onClose: () => void;
	/** Admin solo consulta; el dueño también puede registrar balances. */
	canRecord?: boolean;
};

export function AccountBalancesSheet({
	account,
	onClose,
	canRecord = true,
}: AccountBalancesSheetProps) {
	const [asset, setAsset] = useState('');
	const [recording, setRecording] = useState(false);
	const [lastAccount, setLastAccount] = useState<Account | null>(account);
	const debouncedAsset = useDebouncedValue(asset.trim().toUpperCase(), 300);

	// Se recuerda la última cuenta para que el contenido no se vacíe durante la
	// animación de cierre; cada cuenta nueva abre sin filtro.
	if (account && account.id !== lastAccount?.id) {
		setLastAccount(account);
		setAsset('');
	}
	const current = account ?? lastAccount;

	const balancesQuery = useAccountBalancesQuery(account?.id ?? null, {
		asset: debouncedAsset || undefined,
	});

	return (
		<Sheet open={account !== null} onOpenChange={(open) => !open && onClose()}>
			<SheetContent className="data-[side=right]:w-full data-[side=right]:sm:max-w-2xl">
				<SheetHeader className="pr-14">
					<SheetTitle className="flex flex-wrap items-center gap-2">
						Balances · {current?.name}
						{current && <AccountModeBadge mode={current.mode} />}
					</SheetTitle>
					<SheetDescription>
						Saldos registrados, del más reciente al más antiguo. Moneda base:{' '}
						{current?.base_currency}.
					</SheetDescription>
				</SheetHeader>
				<div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 pb-4">
					<div className="flex flex-wrap items-center gap-2">
						<div className="relative min-w-48 flex-1">
							<IconSearch className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
							<Input
								aria-label="Filtrar por activo"
								placeholder="Filtrar por activo: USDT, BTC"
								value={asset}
								onChange={(event) => setAsset(event.target.value)}
								className="h-10 pl-9"
							/>
						</div>
						{canRecord && (
							<Button size="sm" onClick={() => setRecording(true)}>
								<IconPlus />
								Registrar balance
							</Button>
						)}
					</div>
					<DataTable
						columns={columns}
						rows={balancesQuery.data}
						getRowId={(row) => row.id}
						isLoading={balancesQuery.isLoading}
						error={balancesQuery.error}
						errorTitle="No pudimos cargar los balances"
						empty={
							debouncedAsset
								? `No hay balances de ${debouncedAsset}.`
								: canRecord
									? `Aún no hay balances registrados. Registra el saldo en ${current?.base_currency ?? 'la moneda base'} para que el agente de IA pueda calcular el tamaño de posición.`
									: 'Aún no hay balances registrados.'
						}
					/>
				</div>
				<RecordBalanceDialog
					open={recording}
					onOpenChange={setRecording}
					account={current}
					defaultAsset={debouncedAsset || undefined}
				/>
			</SheetContent>
		</Sheet>
	);
}
