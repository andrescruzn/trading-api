import type {
	BillingPeriod,
	FeeTransaction,
	ManagedAccount,
} from '@/modules/billing/api/billing.api';
import {
	BILLING_PERIOD_STATUS_LABELS,
	FEE_STATUS_LABELS,
} from '@/modules/billing/lib/billing-labels';

// Extracto del inversor en CSV: un período por fila con su comisión. Se arma
// en el navegador con lo que ya cargó la página (no hay endpoint propio).

const SEPARATOR = ';'; // Excel en español abre `;` sin preguntar

function cell(value: string | number | null | undefined): string {
	const text = value === null || value === undefined ? '' : String(value);
	return /[;"\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function day(iso: string | null): string {
	return iso ? iso.slice(0, 10) : '';
}

function buildStatementCsv(
	account: ManagedAccount,
	periods: BillingPeriod[],
	fees: FeeTransaction[],
): string {
	const feeByPeriod = new Map(fees.map((fee) => [fee.billing_period_id, fee]));
	const header = [
		'Período',
		'Desde',
		'Hasta',
		'Estado',
		'Equity inicial',
		'Equity final',
		'PnL bruto',
		'Comisión %',
		'Comisión',
		'PnL neto',
		'Estado de la comisión',
		'Cobrada el',
	];
	const rows = [...periods]
		.sort((a, b) => (a.start_ts ?? '').localeCompare(b.start_ts ?? ''))
		.map((period) => {
			const fee = feeByPeriod.get(period.id);
			return [
				period.id,
				day(period.start_ts),
				day(period.end_ts),
				BILLING_PERIOD_STATUS_LABELS[period.status] ?? period.status,
				period.opening_equity,
				period.closing_equity,
				period.gross_pnl,
				period.fee_pct,
				period.fee_amount,
				period.net_pnl,
				fee ? (FEE_STATUS_LABELS[fee.status] ?? fee.status) : '',
				fee ? day(fee.charged_at) : '',
			];
		});
	const title = [
		`Extracto · ${account.name}`,
		`Capital inicial ${account.initial_capital}`,
	];
	return [title, [], header, ...rows]
		.map((row) => row.map(cell).join(SEPARATOR))
		.join('\r\n');
}

function downloadCsv(filename: string, csv: string): void {
	// BOM para que Excel lea bien las tildes
	const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' });
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	link.download = filename;
	link.click();
	URL.revokeObjectURL(url);
}

export { buildStatementCsv, downloadCsv };
