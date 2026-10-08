import { Dialog as DialogPrimitive } from '@base-ui/react/dialog';
import { IconX } from '@tabler/icons-react';
import { cn } from '@/modules/ui/lib/utils';
import * as React from 'react';
import { Button } from '@/modules/ui/components/button';

type DialogContextProps = {
	showCloseButton: boolean;
};

const DialogContext = React.createContext<DialogContextProps | null>(null);

function useDialog() {
	const context = React.useContext(DialogContext);
	if (!context) {
		throw new Error('useDialog must be used within a DialogProvider.');
	}

	return context;
}

function DialogProvider({
	children,
	showCloseButton,
}: React.PropsWithChildren<{
	showCloseButton: boolean;
}>) {
	const contextValue = React.useMemo<DialogContextProps>(
		() => ({
			showCloseButton,
		}),
		[showCloseButton],
	);

	return (
		<DialogContext.Provider value={contextValue}>
			{children}
		</DialogContext.Provider>
	);
}

function Dialog({
	showCloseButton = true,
	...props
}: DialogPrimitive.Root.Props & Partial<DialogContextProps>) {
	return (
		<DialogProvider showCloseButton={showCloseButton}>
			<DialogPrimitive.Root data-slot="dialog" {...props} />
		</DialogProvider>
	);
}

function DialogTrigger({ ...props }: DialogPrimitive.Trigger.Props) {
	return <DialogPrimitive.Trigger data-slot="dialog-trigger" {...props} />;
}

function DialogPortal({ ...props }: DialogPrimitive.Portal.Props) {
	return <DialogPrimitive.Portal data-slot="dialog-portal" {...props} />;
}

function DialogClose({ ...props }: DialogPrimitive.Close.Props) {
	return <DialogPrimitive.Close data-slot="dialog-close" {...props} />;
}

function DialogOverlay({
	className,
	...props
}: DialogPrimitive.Backdrop.Props) {
	return (
		<DialogPrimitive.Backdrop
			data-slot="dialog-overlay"
			className={cn(
				'fixed inset-0 isolate z-50 bg-black/10 duration-100 supports-backdrop-filter:backdrop-blur-xs data-open:animate-in data-open:fade-in-0 data-closed:animate-out data-closed:fade-out-0',
				className,
			)}
			{...props}
		/>
	);
}

function DialogContent({
	className,
	children,
	...props
}: DialogPrimitive.Popup.Props) {
	const { showCloseButton } = useDialog();

	return (
		<DialogPortal>
			<DialogOverlay />
			<DialogPrimitive.Popup
				data-slot="dialog-content"
				className={cn(
					'fixed top-1/2 left-1/2 z-50 flex flex-col w-full max-w-[calc(100%-2rem)] -translate-x-1/2 -translate-y-1/2 gap-6 rounded-xl bg-popover py-6 px-3 text-sm text-popover-foreground ring-1 ring-foreground/10 duration-100 outline-none sm:max-w-md data-open:animate-in data-open:fade-in-0 data-open:zoom-in-95 data-closed:animate-out data-closed:fade-out-0 data-closed:zoom-out-95 max-h-[90vh]',
					className,
				)}
				{...props}
			>
				{children}
				{showCloseButton && (
					<DialogPrimitive.Close
						data-slot="dialog-close"
						render={
							<Button
								variant="ghost"
								className="absolute top-4 right-4"
								size="icon-sm"
							/>
						}
					>
						<IconX />
						<span className="sr-only">Cerrar</span>
					</DialogPrimitive.Close>
				)}
			</DialogPrimitive.Popup>
		</DialogPortal>
	);
}

function DialogBody({
	className,
	children,
	...props
}: React.ComponentProps<'div'>) {
	return (
		<div
			data-slot="dialog-body"
			className={cn('flex-1 overflow-y-auto px-3 pb-3', className)}
			{...props}
		>
			{children}
		</div>
	);
}

function DialogHeader({
	className,
	children,
	...props
}: React.ComponentProps<'div'>) {
	const { showCloseButton } = useDialog();

	return (
		<div
			data-slot="dialog-header"
			className={cn(
				'flex flex-col gap-2',
				showCloseButton ? 'pl-3 pr-15' : 'px-3',
				className,
			)}
			{...props}
		>
			{children}
		</div>
	);
}

function DialogFooter({
	className,
	children,
	...props
}: React.ComponentProps<'div'>) {
	return (
		<div
			data-slot="dialog-footer"
			className={cn(
				'flex flex-wrap-reverse flex-row gap-2 justify-end px-3',
				className,
			)}
			{...props}
		>
			{children}
		</div>
	);
}

function DialogTitle({ className, ...props }: DialogPrimitive.Title.Props) {
	return (
		<DialogPrimitive.Title
			data-slot="dialog-title"
			className={cn('font-heading leading-none font-medium', className)}
			{...props}
		/>
	);
}

function DialogDescription({
	className,
	...props
}: DialogPrimitive.Description.Props) {
	return (
		<DialogPrimitive.Description
			data-slot="dialog-description"
			className={cn(
				'text-sm text-muted-foreground *:[a]:underline *:[a]:underline-offset-3 *:[a]:hover:text-foreground',
				className,
			)}
			{...props}
		/>
	);
}

export {
	Dialog,
	DialogBody,
	DialogClose,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogOverlay,
	DialogPortal,
	DialogTitle,
	DialogTrigger,
};
