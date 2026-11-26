import { zodResolver } from '@hookform/resolvers/zod';
import { IconBrandTelegram, IconLoader2, IconSend } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import type {
	TelegramSettings,
	TelegramUpdatesMode,
} from '@/modules/notifications/api/notification-settings.api';
import { ChannelStatusBadge } from '@/modules/notifications/components/channel-status-badge';
import {
	useSendTelegramTestMutation,
	useUpdateTelegramSettingsMutation,
} from '@/modules/notifications/hooks/use-notification-settings-mutations';
import {
	suggestedWebhookUrl,
	UPDATES_MODE_DESCRIPTIONS,
	UPDATES_MODE_OPTIONS,
} from '@/modules/notifications/lib/notifications-labels';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { getErrorMessage } from '@/modules/shared/lib/get-error-message';
import { Button } from '@/modules/ui/components/button';
import {
	Card,
	CardAction,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';
import { Checkbox } from '@/modules/ui/components/checkbox';
import {
	Field,
	FieldContent,
	FieldDescription,
	FieldError,
	FieldGroup,
	FieldLabel,
} from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';
import { toast } from '@/modules/ui/components/toast';

// Mismas reglas que UpdateTelegramSettingsService (backend)
const TOKEN_RE = /^\d{5,20}:[A-Za-z0-9_-]{30,64}$/;
const CHAT_ID_RE = /^(-?\d{1,20}|@[A-Za-z0-9_]{5,32})$/;

function buildSchema(tokenSaved: boolean) {
	return z
		.object({
			enabled: z.boolean(),
			bot_token: z.string().trim().max(128),
			default_chat_id: z.string().trim().max(64),
			updates_mode: z.enum(['off', 'polling', 'webhook']),
			webhook_url: z.string().trim().max(2048),
		})
		.superRefine((values, ctx) => {
			if (values.bot_token && !TOKEN_RE.test(values.bot_token)) {
				ctx.addIssue({
					code: 'custom',
					path: ['bot_token'],
					message:
						'El token tiene la forma 123456789:ABC… Cópialo de @BotFather.',
				});
			}
			if (values.enabled && !values.bot_token && !tokenSaved) {
				ctx.addIssue({
					code: 'custom',
					path: ['bot_token'],
					message: 'Escribe el token del bot para activar Telegram.',
				});
			}
			if (values.default_chat_id && !CHAT_ID_RE.test(values.default_chat_id)) {
				ctx.addIssue({
					code: 'custom',
					path: ['default_chat_id'],
					message:
						'Usa un ID numérico (los grupos empiezan por -) o un @canal.',
				});
			}
			if (
				values.updates_mode === 'webhook' &&
				!values.webhook_url.startsWith('https://')
			) {
				ctx.addIssue({
					code: 'custom',
					path: ['webhook_url'],
					message:
						'Escribe la URL pública de la API; debe empezar por https://.',
				});
			}
		});
}

type TelegramFormValues = z.output<ReturnType<typeof buildSchema>>;

function toFormValues(settings: TelegramSettings): TelegramFormValues {
	return {
		enabled: settings.enabled,
		bot_token: '',
		default_chat_id: settings.default_chat_id ?? '',
		updates_mode: settings.updates_mode,
		webhook_url: settings.webhook_url ?? '',
	};
}

type TelegramSettingsCardProps = {
	settings: TelegramSettings;
	/** El socio ve la configuración sin poder cambiarla. */
	readOnly: boolean;
};

export function TelegramSettingsCard({
	settings,
	readOnly,
}: TelegramSettingsCardProps) {
	const updateMutation = useUpdateTelegramSettingsMutation();
	const testMutation = useSendTelegramTestMutation();
	const form = useForm<TelegramFormValues>({
		resolver: zodResolver(buildSchema(settings.token_set)),
		defaultValues: toFormValues(settings),
	});
	const updatesMode = useWatch({ control: form.control, name: 'updates_mode' });

	useEffect(() => {
		form.reset(toFormValues(settings));
	}, [settings, form]);

	function handleSubmit(values: TelegramFormValues) {
		updateMutation.mutate(
			{
				enabled: values.enabled,
				bot_token: values.bot_token || null,
				default_chat_id: values.default_chat_id || null,
				updates_mode: values.updates_mode,
				webhook_url:
					values.updates_mode === 'webhook' ? values.webhook_url : null,
			},
			{
				onSuccess: () =>
					toast.add({ title: 'Telegram guardado', type: 'success' }),
				onError: (error) =>
					toast.add({
						title: 'No pudimos guardar Telegram',
						description: getErrorMessage(error),
						type: 'error',
					}),
			},
		);
	}

	function handleTest() {
		testMutation.mutate(undefined, {
			onSuccess: (result) =>
				toast.add({
					title: 'Mensaje de prueba enviado',
					description:
						result.target === 'own_chat'
							? 'Revisa tu chat de Telegram.'
							: 'Revisa el chat por defecto.',
					type: 'success',
				}),
			onError: (error) =>
				toast.add({
					title: 'No pudimos enviar la prueba',
					description: getErrorMessage(error),
					type: 'error',
				}),
		});
	}

	return (
		<Card>
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<IconBrandTelegram className="size-5" />
					Telegram
				</CardTitle>
				<CardDescription>
					Señales por aprobar con botones, señales de agentes que siguen,
					alertas y avisos del fondo. Cada persona conecta su chat desde el menú
					de usuario.
				</CardDescription>
				<CardAction>
					<ChannelStatusBadge
						active={settings.active}
						configured={settings.token_set}
					/>
				</CardAction>
			</CardHeader>
			<form onSubmit={form.handleSubmit(handleSubmit)} noValidate>
				<CardContent>
					<FieldGroup>
						<Controller
							name="enabled"
							control={form.control}
							render={({ field }) => (
								<Field orientation="horizontal">
									<Checkbox
										id="telegram-enabled"
										checked={field.value}
										disabled={readOnly}
										onCheckedChange={(checked) => field.onChange(checked)}
									/>
									<FieldContent>
										<FieldLabel htmlFor="telegram-enabled">
											Enviar avisos por Telegram
										</FieldLabel>
										<FieldDescription>
											Apagado, no sale ningún mensaje y el bot no responde.
										</FieldDescription>
									</FieldContent>
								</Field>
							)}
						/>
						<div className="grid gap-4 md:grid-cols-2">
							<Controller
								name="bot_token"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="telegram-token">
											Token del bot
										</FieldLabel>
										<Input
											{...field}
											id="telegram-token"
											type="password"
											autoComplete="off"
											placeholder={
												settings.token_hint
													? `Guardado: ••••${settings.token_hint}`
													: '123456789:ABC…'
											}
											disabled={readOnly}
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											{settings.token_set
												? 'Déjalo vacío para conservar el guardado.'
												: 'Créalo con @BotFather en Telegram.'}
										</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Field>
								<FieldLabel htmlFor="telegram-username">Bot</FieldLabel>
								<Input
									id="telegram-username"
									value={
										settings.bot_username ? `@${settings.bot_username}` : ''
									}
									placeholder="Se detecta al guardar el token"
									readOnly
									disabled
								/>
								<FieldDescription>
									Con este nombre cada persona encuentra el bot al conectar su
									chat.
								</FieldDescription>
							</Field>
							<Controller
								name="default_chat_id"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="telegram-chat">
											Chat por defecto
										</FieldLabel>
										<Input
											{...field}
											id="telegram-chat"
											placeholder="-1001234567890"
											disabled={readOnly}
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Opcional. Recibe las alertas de quien no conectó su
											Telegram. Vacío = no se envían.
										</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
							<Controller
								name="updates_mode"
								control={form.control}
								render={({ field }) => (
									<Field>
										<FieldLabel htmlFor="telegram-mode">
											Respuestas del bot
										</FieldLabel>
										<OptionSelect
											id="telegram-mode"
											value={field.value}
											onChange={(value) => {
												const mode = (value ?? 'off') as TelegramUpdatesMode;
												field.onChange(mode);
												if (
													mode === 'webhook' &&
													!form.getValues('webhook_url')
												) {
													form.setValue('webhook_url', suggestedWebhookUrl());
												}
											}}
											options={UPDATES_MODE_OPTIONS}
											disabled={readOnly}
										/>
										<FieldDescription>
											{UPDATES_MODE_DESCRIPTIONS[field.value]}
										</FieldDescription>
									</Field>
								)}
							/>
						</div>
						{updatesMode === 'webhook' && (
							<Controller
								name="webhook_url"
								control={form.control}
								render={({ field, fieldState }) => (
									<Field data-invalid={fieldState.invalid}>
										<FieldLabel htmlFor="telegram-webhook">
											URL del webhook
										</FieldLabel>
										<Input
											{...field}
											id="telegram-webhook"
											placeholder="https://api.tudominio.com/api/telegram/webhook"
											disabled={readOnly}
											aria-invalid={fieldState.invalid}
										/>
										<FieldDescription>
											Dirección pública de la API terminada en
											/api/telegram/webhook. Al guardar, la registramos en
											Telegram con una clave secreta.
										</FieldDescription>
										{fieldState.invalid && (
											<FieldError errors={[fieldState.error]} />
										)}
									</Field>
								)}
							/>
						)}
					</FieldGroup>
				</CardContent>
				{!readOnly && (
					<CardFooter className="flex-wrap justify-end gap-2">
						<Button
							type="button"
							variant="outline"
							onClick={handleTest}
							disabled={!settings.active || testMutation.isPending}
						>
							{testMutation.isPending ? (
								<IconLoader2 className="animate-spin" />
							) : (
								<IconSend />
							)}
							Enviar prueba
						</Button>
						<Button type="submit" disabled={updateMutation.isPending}>
							{updateMutation.isPending && (
								<IconLoader2 className="animate-spin" />
							)}
							Guardar Telegram
						</Button>
					</CardFooter>
				)}
			</form>
		</Card>
	);
}
