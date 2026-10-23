import { IconAlertTriangle } from '@tabler/icons-react';
import type { DepositInfo } from '@/modules/fund/api/fund.api';
import { CopyText } from '@/modules/fund/components/copy-text';
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from '@/modules/ui/components/alert';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/modules/ui/components/card';

/** Cómo depositar: a qué dirección y por qué red, paso a paso. */
export function DepositInstructions({ info }: { info: DepositInfo }) {
	const asset = info.asset ?? 'USDT';

	return (
		<Card>
			<CardHeader>
				<CardTitle>Cómo depositar</CardTitle>
				<CardDescription>
					1. Envía {asset} a la dirección de la red que elijas. 2. Copia el hash
					de la transacción (txid) de tu billetera. 3. Pulsa «Registrar
					depósito». Lo confirmamos en cuanto aparezca en el exchange.
				</CardDescription>
			</CardHeader>
			<CardContent className="flex flex-col gap-4">
				<ul className="flex flex-col gap-3">
					{info.networks.map((network) => (
						<li
							key={network.network}
							className="flex flex-col gap-1 rounded-lg border p-3"
						>
							<span className="text-sm font-medium">
								{asset} por {network.name}{' '}
								<span className="text-muted-foreground">
									({network.network})
								</span>
							</span>
							<CopyText value={network.address} label="Dirección" />
							{network.tag && (
								<span className="flex flex-wrap items-center gap-1 text-sm">
									<span className="font-medium text-destructive">
										Memo obligatorio:
									</span>
									<CopyText value={network.tag} label="Memo" />
								</span>
							)}
						</li>
					))}
				</ul>
				<Alert>
					<IconAlertTriangle />
					<AlertTitle>Usa la misma red al enviar</AlertTitle>
					<AlertDescription>
						Si envías por otra red o sin el memo, el dinero puede perderse.
						Envía solo {asset}. El depósito pasa a «Pendiente de asignar» y debe
						estar al menos {info.min_hold_days} días en un agente antes de poder
						retirarlo.
					</AlertDescription>
				</Alert>
			</CardContent>
		</Card>
	);
}
