import { IconAlertTriangle, IconLoader2, IconPlus } from '@tabler/icons-react';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
import type { Account } from '@/modules/accounts/api/accounts.api';
import {
	useCreateAccountMutation,
	useRecordBalanceMutation,
} from '@/modules/accounts/hooks/use-accounts-mutations';
import { useAccountBalancesQuery } from '@/modules/accounts/hooks/use-accounts-queries';
import { ChoiceCard } from '@/modules/bots/components/agent-wizard/choice-card';
import { BotModeBadge } from '@/modules/bots/components/bot-badges';
import { formatNumber, toNumber } from '@/modules/shared/lib/format';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import { Button } from '@/modules/ui/components/button';
import {
	Field,
	FieldDescription,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { Skeleton } from '@/modules/ui/components/skeleton';
import { toast } from '@/modules/ui/components/toast';

/** Saldo libre más reciente en la moneda base de la cuenta. */
function useFreeBalance(account: Account) {
	const query = useAccountBalancesQuery(account.id, {
		asset: account.base_currency,
		limit: 1,
	});
	const free = toNumber(query.data?.[0]?.free ?? null);
	return { free, isLoading: query.isLoading };
}

function AccountChoice({
	account,
	selected,
	onSelect,
}: {
	account: Account;
	selected: boolean;
	onSelect: () => void;
}) {
	const { free, isLoading } = useFreeBalance(account);
	const hasBalance = free !== null && free > 0;

	return (
		<ChoiceCard
			selected={selected}
			onSelect={onSelect}
			eyebrow={`Moneda base: ${account.base_currency}`}
			title={account.name}
			description={
				isLoading ? (
					<Skeleton className="h-4 w-28" />
				) : hasBalance ? (
					<span className="font-mono tabular-nums">
						{formatNumber(free)} {account.base_currency} disponibles
					</span>
				) : (
					<span className="text-destructive">
						Sin saldo en {account.base_currency}
					</span>
				)
			}
			footer={<BotModeBadge mode={account.mode} />}
		/>
	);
}

/** Crea una cuenta paper con su saldo inicial en un solo paso. */
function PracticeAccountForm({
	currency,
	onCreated,
	onCancel,
}: {
	currency: string;
	onCreated: (account: Account) => void;
	onCancel?: () => void;
}) {
	const createAccount = useCreateAccountMutation();
	const recordBalance = useRecordBalanceMutation();
	const [name, setName] = useState('Cuenta de práctica');
	const [capital, setCapital] = useState('10000');
	const capitalNumber = Number(capital);
	const isValid = name.trim().length > 0 && capitalNumber > 0;
	const isPending = createAccount.isPending || recordBalance.isPending;

	async function handleCreate() {
		try {
			const account = await createAccount.mutateAsync({
				name: name.trim(),
				mode: 'paper',
				base_currency: currency,
				exchange_id: null,
			});
			await recordBalance.mutateAsync({
				accountId: account.id,
				input: { asset: currency, free: String(capitalNumber), locked: '0' },
			});
			toast.add({ title: 'Cuenta de práctica creada', type: 'success' });
			onCreated(account);
		} catch (error) {
			toast.add({
				title: 'No pudimos crear la cuenta',
				description: getErrorMessage(error),
				type: 'error',
			});
		}
	}

	return (
		<div className="flex flex-col gap-4 rounded-xl border border-dashed bg-muted/30 p-5">
			<div>
				<p className="font-medium">Cuenta de práctica (paper)</p>
				<p className="text-sm text-muted-foreground">
					Simula operaciones con dinero ficticio. Es la forma segura de probar
					un agente antes de usar dinero real.
				</p>
			</div>
			<div className="grid gap-4 sm:grid-cols-2">
				<Field>
					<FieldLabel htmlFor="practice-name" required>
						Nombre
					</FieldLabel>
					<Input
						id="practice-name"
						value={name}
						maxLength={120}
						onChange={(event) => setName(event.target.value)}
					/>
				</Field>
				<Field>
					<FieldLabel htmlFor="practice-capital" required>
						Capital inicial ({currency})
					</FieldLabel>
					<Input
						id="practice-capital"
						type="number"
						inputMode="decimal"
						min="1"
						value={capital}
						onChange={(event) => setCapital(event.target.value)}
					/>
					<FieldDescription>
						Con la regla del 1 %, cada operación arriesga como máximo{' '}
						{capitalNumber > 0
							? `${formatNumber(capitalNumber * 0.01)} ${currency}`
							: '—'}
						.
					</FieldDescription>
				</Field>
			</div>
			<div className="flex justify-end gap-2">
				{onCancel && (
					<Button variant="ghost" size="sm" onClick={onCancel}>
						Cancelar
					</Button>
				)}
				<Button
					size="sm"
					onClick={handleCreate}
					disabled={!isValid || isPending}
				>
					{isPending ? <IconLoader2 className="animate-spin" /> : <IconPlus />}
					Crear cuenta
				</Button>
			</div>
		</div>
	);
}

type AccountStepProps = {
	/** Cuentas propias y activas del usuario. */
	accounts: Account[];
	isLoading: boolean;
	value: string | null;
	onChange: (value: string) => void;
	/** Moneda de cotización del símbolo elegido: base de la cuenta de práctica. */
	currency: string;
	/** Por qué no aparecen algunas cuentas live (otro exchange o perpetuo). */
	hiddenLiveNote?: string;
};

/** Paso 3: con qué dinero opera el agente. Su modo (paper/live) es el de la cuenta. */
export function AccountStep({
	accounts,
	isLoading,
	value,
	onChange,
	currency,
	hiddenLiveNote,
}: AccountStepProps) {
	const [showPracticeForm, setShowPracticeForm] = useState(false);
	const selected = accounts.find((account) => String(account.id) === value);
	const hiddenNote = hiddenLiveNote && (
		<p className="text-sm text-muted-foreground">{hiddenLiveNote}</p>
	);

	if (isLoading) {
		return (
			<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
				<Skeleton className="h-28 rounded-xl" />
				<Skeleton className="h-28 rounded-xl" />
			</div>
		);
	}

	if (accounts.length === 0) {
		return (
			<div className="flex flex-col gap-4">
				{hiddenNote ?? (
					<p className="text-sm text-muted-foreground">
						Aún no tienes cuentas. Crea una de práctica para empezar; luego
						podrás conectar una cuenta real desde{' '}
						<Link to="/portfolio" className="text-primary hover:underline">
							Mis cuentas
						</Link>
						.
					</p>
				)}
				<PracticeAccountForm
					currency={currency}
					onCreated={(account) => onChange(String(account.id))}
				/>
			</div>
		);
	}

	return (
		<div className="flex flex-col gap-4">
			{hiddenNote}
			<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
				{accounts.map((account) => (
					<AccountChoice
						key={account.id}
						account={account}
						selected={value === String(account.id)}
						onSelect={() => onChange(String(account.id))}
					/>
				))}
				{!showPracticeForm && (
					<button
						type="button"
						onClick={() => setShowPracticeForm(true)}
						className="flex min-h-28 flex-col items-center justify-center gap-1 rounded-xl border border-dashed p-4 text-sm text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
					>
						<IconPlus className="size-5" />
						Nueva cuenta de práctica
					</button>
				)}
			</div>

			{showPracticeForm && (
				<PracticeAccountForm
					currency={currency}
					onCancel={() => setShowPracticeForm(false)}
					onCreated={(account) => {
						setShowPracticeForm(false);
						onChange(String(account.id));
					}}
				/>
			)}

			{selected?.mode === 'live' && (
				<Alert variant="destructive">
					<IconAlertTriangle />
					<AlertTitle>Esta cuenta usa dinero real</AlertTitle>
					<AlertDescription>
						Las órdenes del agente se enviarán al exchange. Te recomendamos
						probarlo primero con una cuenta de práctica.
					</AlertDescription>
				</Alert>
			)}
		</div>
	);
}
