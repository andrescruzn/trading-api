export function scrollToFirstInvalidField(formId: string) {
	requestAnimationFrame(() => {
		document
			.getElementById(formId)
			?.querySelector('[data-invalid="true"]')
			?.scrollIntoView({ behavior: 'auto', block: 'center' });
	});
}
