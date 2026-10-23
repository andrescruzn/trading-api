import {
	type FundPool,
	type LedgerEntry,
	listMyLedger,
} from '@/modules/fund/api/fund.api';
import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (F6: resumen del fondo, mis ganancias y comprobantes). Montos como
// string (DECIMAL del backend).
// ======================================================================

/** Lo que ganó una persona: comisiones recibidas + su dinero como inversor. */
type ParticipantSummary = {
	user_id: number;
	commissions: string;
	/** Ganancia de lo que ya salió de los agentes (antes de comisión). */
	realized_gain: string;
	fees_paid: string;
	in_agents_cost: string;
	/** A la última liquidación de cada agente. */
	in_agents_value: string;
	unrealized_gain: string;
	pending: string;
	available: string;
	/** Comisiones + ganancia realizada − comisión pagada + no realizada. */
	total_earned: string;
};

type FundOverview = {
	asset: string;
	wallet: {
		total_value: string;
		free_value: string;
		locked_value: string;
		missing_prices: string[];
		ts: string | null;
	} | null;
	last_synced_at: string | null;
	last_sync_error: string | null;
	agents: FundPool[];
	agents_capital: string;
	pending_total: string;
	available_total: string;
	/** Capital de los agentes + pendiente + disponible. */
	accounted: string;
	/** Billetera − lo que tiene dueño; `null` sin foto de la billetera. */
	difference: string | null;
	queued_allocations: string;
	open_withdrawals_count: number;
	open_withdrawals_total: string;
	deposits_waiting_count: number;
	deposits_waiting_total: string;
	owners: ParticipantSummary[];
};

type ReceiptFile = { filename: string; data_base64: string };

type WithdrawalReceipt = ReceiptFile & {
	withdrawal_id: number;
	content_type: string;
	size_bytes: number;
	created_at: string | null;
};

function getFundOverview() {
	return api.get<FundOverview>('/fund/overview');
}

function getMySummary() {
	return api.get<ParticipantSummary>('/fund/me/summary');
}

// Tope del extracto: 50 páginas de 100 movimientos
const MAX_EXPORT_PAGES = 50;

/** Todo mi libro (para el extracto CSV), página por página. */
async function listAllMyLedger(): Promise<LedgerEntry[]> {
	const entries: LedgerEntry[] = [];
	for (let page = 1; page <= MAX_EXPORT_PAGES; page++) {
		const result = await listMyLedger({ page, page_size: 100 });
		entries.push(...result.items);
		if (page >= result.pagination.total_pages) break;
	}
	return entries;
}

function getWithdrawalReceipt(id: number) {
	return api.get<WithdrawalReceipt>(`/fund/withdrawals/${id}/receipt`);
}

export type {
	FundOverview,
	ParticipantSummary,
	ReceiptFile,
	WithdrawalReceipt,
};
export { getFundOverview, getMySummary, getWithdrawalReceipt, listAllMyLedger };
