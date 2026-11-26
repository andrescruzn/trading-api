import type { LedgerEntry } from '@/modules/fund/api/fund.api';
import type {
	ReceiptFile,
	WithdrawalReceipt,
} from '@/modules/fund/api/fund-overview.api';
import {
	LEDGER_BUCKET_LABELS,
	LEDGER_ENTRY_TYPE_LABELS,
} from '@/modules/fund/lib/fund-labels';
import { formatTimestamp } from '@/modules/shared/lib/format';
import { saveBlob } from '@/modules/shared/lib/save-blob';

/** Mismo límite y tipos que el backend (se valida también por el contenido). */
const MAX_RECEIPT_BYTES = 5 * 1024 * 1024;
const RECEIPT_ACCEPT = 'application/pdf,image/png,image/jpeg';

/** Valida tamaño en el navegador; el tipo real lo valida el backend. */
function receiptFileError(file: File | null): string | null {
	if (file && file.size > MAX_RECEIPT_BYTES) {
		return 'El archivo pesa más de 5 MB. Sube uno más liviano.';
	}
	return null;
}

/** Archivo → `{filename, data_base64}` para enviarlo en el JSON. */
function fileToReceipt(file: File): Promise<ReceiptFile> {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = () => {
			// `data:<tipo>;base64,<datos>` → solo los datos
			const result = String(reader.result ?? '');
			resolve({
				filename: file.name,
				data_base64: result.slice(result.indexOf(',') + 1),
			});
		};
		reader.onerror = () => reject(reader.error);
		reader.readAsDataURL(file);
	});
}

function downloadReceipt(receipt: WithdrawalReceipt) {
	const bytes = Uint8Array.from(atob(receipt.data_base64), (char) =>
		char.charCodeAt(0),
	);
	saveBlob(new Blob([bytes], { type: receipt.content_type }), receipt.filename);
}

function csvCell(value: string | number | null | undefined) {
	const text = value == null ? '' : String(value);
	return /[",;\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

/**
 * Extracto del libro en CSV (separador `;` y coma decimal para que Excel en
 * español lo abra en columnas). El BOM hace que lea bien las tildes.
 */
function downloadLedgerCsv(entries: LedgerEntry[], fileName: string) {
	const header = [
		'Fecha (hora de Colombia)',
		'Movimiento',
		'Saldo',
		'Monto',
		'Moneda',
		'Detalle',
	];
	const rows = entries.map((entry) => [
		formatTimestamp(entry.created_at),
		LEDGER_ENTRY_TYPE_LABELS[entry.entry_type] ?? entry.entry_type,
		LEDGER_BUCKET_LABELS[entry.bucket] ?? entry.bucket,
		entry.amount.replace('.', ','),
		entry.asset,
		entry.description ?? '',
	]);
	const csv = [header, ...rows]
		.map((row) => row.map(csvCell).join(';'))
		.join('\n');
	saveBlob(new Blob([`﻿${csv}`], { type: 'text/csv;charset=utf-8' }), fileName);
}

export {
	downloadLedgerCsv,
	downloadReceipt,
	fileToReceipt,
	MAX_RECEIPT_BYTES,
	RECEIPT_ACCEPT,
	receiptFileError,
};
