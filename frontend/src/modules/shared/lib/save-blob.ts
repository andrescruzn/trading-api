/** Dispara la descarga de un `Blob` en el navegador con el nombre de archivo indicado. */
function saveBlob(blob: Blob, fileName: string) {
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');

	link.href = url;
	link.download = fileName;
	document.body.append(link);
	link.click();
	link.remove();

	// Revocar de inmediato puede cancelar la descarga en algunos navegadores.
	setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export { saveBlob };
