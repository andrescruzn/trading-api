import { IconFileDownload, IconLoader2 } from '@tabler/icons-react';
import { useMutation } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { getWithdrawalReceipt } from '@/modules/fund/api/fund-overview.api';
import type { Withdrawal } from '@/modules/fund/api/fund-payouts.api';
import { useAttachReceiptMutation } from '@/modules/fund/hooks/use-fund-payouts-mutations';
import {
	downloadReceipt,
	fileToReceipt,
	RECEIPT_ACCEPT,
	receiptFileError,
} from '@/modules/fund/lib/fund-files';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button } from '@/modules/ui/components/button';
import {
	Dialog,
	DialogBody,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from '@/modules/ui/components/dialog';
import {
	Field,
	FieldDescription,
	FieldError,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

type ReceiptFieldProps = {
	id: string;
	file: File | null;
	onChange: (file: File | null) => void;
	required?: boolean;
};

/** Campo de archivo del comprobante (PDF, PNG o JPG, máx. 5 MB). */
function ReceiptField({ id, file, onChange, required }: ReceiptFieldProps) {
	const error = receiptFileError(file);
	return (
		<Field data-invalid={!!error}>
			<FieldLabel htmlFor={id} required={required}>
				Comprobante{required ? '' : ' (opcional)'}
			</FieldLabel>
			<Input
				id={id}
				type="file"
				accept={RECEIPT_ACCEPT}
				aria-invalid={!!error}
				onChange={(event) => onChange(event.target.files?.[0] ?? null)}
			/>
			<FieldDescription>
				PDF, PNG o JPG de hasta 5 MB. La persona lo puede descargar.
			</FieldDescription>
			{error && <FieldError errors={[{ message: error }]} />}
		</Field>
	);
}

/** Descarga el comprobante de un retiro (la persona o el staff). */
function ReceiptDownloadButton({ withdrawal }: { withdrawal: Withdrawal }) {
	const mutation = useMutation({ mutationFn: getWithdrawalReceipt });
	return (
		<Button
			variant="ghost"
			size="sm"
			disabled={mutation.isPending}
			onClick={(event) => {
				event.stopPropagation();
				mutation.mutate(withdrawal.id, {
					onSuccess: downloadReceipt,
					onError: (error) =>
						toast.add({
							title: 'No pudimos descargar el comprobante',
							description: getErrorMessage(error),
							type: 'error',
						}),
				});
			}}
		>
			{mutation.isPending ? (
				<IconLoader2 className="animate-spin" />
			) : (
				<IconFileDownload />
			)}
			Comprobante
		</Button>
	);
}

type AttachReceiptDialogProps = {
	withdrawal: Withdrawal | null;
	onClose: () => void;
};

/** Adjunta o cambia el comprobante de un retiro ya pagado (super admin). */
function AttachReceiptDialog({
	withdrawal,
	onClose,
}: AttachReceiptDialogProps) {
	const mutation = useAttachReceiptMutation();
	const [file, setFile] = useState<File | null>(null);

	useEffect(() => {
		if (withdrawal) setFile(null);
	}, [withdrawal]);

	async function submit() {
		if (!withdrawal || !file || receiptFileError(file)) return;
		const receipt = await fileToReceipt(file);
		mutation.mutate(
			{ id: withdrawal.id, receipt },
			{
				onSuccess: () => {
					toast.add({ title: 'Comprobante guardado', type: 'success' });
					onClose();
				},
				onError: (error) =>
					toast.add({
						title: 'No pudimos guardar el comprobante',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	return (
		<Dialog open={!!withdrawal} onOpenChange={(open) => !open && onClose()}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>
						{withdrawal?.receipt_name
							? 'Cambiar comprobante'
							: 'Adjuntar comprobante'}
					</DialogTitle>
					<DialogDescription>
						{withdrawal?.receipt_name
							? `Reemplaza «${withdrawal.receipt_name}».`
							: 'El comprobante de la transferencia de este retiro.'}
					</DialogDescription>
				</DialogHeader>
				<DialogBody>
					<ReceiptField
						id="attach-receipt"
						file={file}
						onChange={setFile}
						required
					/>
				</DialogBody>
				<DialogFooter>
					<Button variant="outline" onClick={onClose}>
						Cancelar
					</Button>
					<Button
						onClick={submit}
						disabled={!file || !!receiptFileError(file) || mutation.isPending}
					>
						{mutation.isPending && <IconLoader2 className="animate-spin" />}
						Guardar comprobante
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}

export { AttachReceiptDialog, ReceiptDownloadButton, ReceiptField };
