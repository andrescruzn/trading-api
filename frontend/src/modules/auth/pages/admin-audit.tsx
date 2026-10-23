import { IconRefresh, IconSearch } from '@tabler/icons-react';
import { useState } from 'react';
import { usePageBreadcrumb } from '@/modules/app-shell/hooks/use-page-breadcrumb';
import type {
	AuditEvent,
	AuditEventsFilters,
	AuditEventType,
	AuditKind,
} from '@/modules/auth/api/audit.api';
import { AuditEventSheet } from '@/modules/auth/components/audit-event-sheet';
import { OwnerCell } from '@/modules/auth/components/owner-cell';
import { useAuditEventsQuery } from '@/modules/auth/hooks/use-audit-queries';
import { useOwners } from '@/modules/auth/hooks/use-users-queries';
import {
	AUDIT_EVENT_TYPE_OPTIONS,
	AUDIT_KIND_OPTIONS,
	auditEventTypeLabel,
	isErrorStatus,
} from '@/modules/auth/lib/audit-labels';
import {
	DataTable,
	type DataTableColumn,
} from '@/modules/shared/components/data-table';
import { OptionSelect } from '@/modules/shared/components/option-select';
import { PageListHeader } from '@/modules/shared/components/page-list-header';
import { TablePagination } from '@/modules/shared/components/table-pagination';
import { useDebouncedValue } from '@/modules/shared/hooks/use-debounced-value';
import {
	formatDateTimeSeconds,
	startOfAppDayIso,
	startOfNextAppDayIso,
} from '@/modules/shared/lib/format';
import { DEFAULT_PAGE_LIMIT, type PageLimit } from '@/modules/shared/types/api';
import { Badge } from '@/modules/ui/components/badge';
import { Field, FieldLabel } from '@/modules/ui/components/field';
import { Input } from '@/modules/ui/components/input';

const ALL = 'all';
const ERRORS = 'errors';

const EVENT_TYPE_FILTER_OPTIONS = [
	{ value: ALL, label: 'Todos los eventos' },
	...AUDIT_EVENT_TYPE_OPTIONS,
];

const KIND_FILTER_OPTIONS = [
	{ value: ALL, label: 'Consultas y cambios' },
	...AUDIT_KIND_OPTIONS,
];

const RESULT_FILTER_OPTIONS = [
	{ value: ALL, label: 'Todos los resultados' },
	{ value: ERRORS, label: 'Solo errores' },
];

type Filters = {
	owner: string;
	eventType: string;
	kind: string;
	result: string;
	dateFrom: string;
	dateTo: string;
};

const INITIAL_FILTERS: Filters = {
	owner: ALL,
	eventType: ALL,
	kind: ALL,
	result: ALL,
	dateFrom: '',
	dateTo: '',
};

export function AdminAuditPage() {
	usePageBreadcrumb([{ label: 'Administración' }, { label: 'Auditoría' }]);
	const owners = useOwners(ALL);
	const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);
	const [path, setPath] = useState('');
	const [page, setPage] = useState(1);
	const [limit, setLimit] = useState<PageLimit>(DEFAULT_PAGE_LIMIT);
	const [selected, setSelected] = useState<AuditEvent | null>(null);
	const debouncedPath = useDebouncedValue(path.trim(), 300);

	// Cada filtro nuevo vuelve a la primera página.
	function updateFilter<K extends keyof Filters>(key: K, value: Filters[K]) {
		setFilters((current) => ({ ...current, [key]: value }));
		setPage(1);
	}

	const rangeInvalid =
		!!filters.dateFrom && !!filters.dateTo && filters.dateTo < filters.dateFrom;

	// Las fechas del filtro son días de tu zona horaria: se envían como ISO con
	// offset y "hasta" incluye todo ese día (el backend la trata como exclusiva).
	const query: AuditEventsFilters = {
		page,
		page_size: limit,
		user_id: filters.owner === ALL ? undefined : Number(filters.owner),
		event_type:
			filters.eventType === ALL
				? undefined
				: (filters.eventType as AuditEventType),
		kind: filters.kind === ALL ? undefined : (filters.kind as AuditKind),
		only_errors: filters.result === ERRORS ? true : undefined,
		path: debouncedPath || undefined,
		date_from: filters.dateFrom
			? startOfAppDayIso(filters.dateFrom)
			: undefined,
		date_to: filters.dateTo ? startOfNextAppDayIso(filters.dateTo) : undefined,
	};
	const eventsQuery = useAuditEventsQuery(query, { enabled: !rangeInvalid });
	const data = rangeInvalid ? undefined : eventsQuery.data;

	const hasFilters =
		debouncedPath !== '' ||
		(Object.keys(INITIAL_FILTERS) as (keyof Filters)[]).some(
			(key) => filters[key] !== INITIAL_FILTERS[key],
		);

	const columns: DataTableColumn<AuditEvent>[] = [
		{
			id: 'ts',
			header: 'Fecha',
			className: 'whitespace-nowrap',
			cell: (row) => formatDateTimeSeconds(row.ts),
			skeletonClassName: 'w-36',
		},
		{
			id: 'user',
			header: 'Persona',
			skeletonClassName: 'w-40',
			cell: (row) =>
				row.user_id != null ? (
					<OwnerCell userId={row.user_id} users={owners.byId} />
				) : (
					<div className="flex flex-col">
						<span className="text-muted-foreground">Sin sesión</span>
						{row.login_email && (
							<span className="text-xs text-muted-foreground">
								{row.login_email}
							</span>
						)}
					</div>
				),
		},
		{
			id: 'event',
			header: 'Evento',
			skeletonClassName: 'w-48',
			cell: (row) => (
				<div className="flex min-w-0 flex-col">
					<span>{auditEventTypeLabel(row.event_type)}</span>
					<span className="max-w-80 truncate font-mono text-xs text-muted-foreground">
						{row.method} {row.path}
					</span>
				</div>
			),
		},
		{
			id: 'status',
			header: 'Resultado',
			cell: (row) => (
				<Badge
					variant={isErrorStatus(row.status_code) ? 'destructive' : 'outline'}
				>
					{row.status_code}
				</Badge>
			),
		},
		{
			id: 'duration',
			header: 'Duración',
			className: 'text-right font-mono tabular-nums whitespace-nowrap',
			cell: (row) =>
				row.duration_ms != null
					? `${row.duration_ms.toLocaleString('es-CO')} ms`
					: '—',
		},
	];

	return (
		<div className="flex flex-col gap-6">
			<PageListHeader
				title="Auditoría"
				description="Cada acción en la app queda registrada: quién la hizo, cuándo y con qué resultado. Los códigos de entrada y las claves de API nunca se guardan."
				actions={[
					{
						label: 'Actualizar',
						icon: <IconRefresh />,
						variant: 'outline',
						onClick: () => eventsQuery.refetch(),
						disabled: eventsQuery.isFetching || rangeInvalid,
					},
				]}
			/>
			<div className="flex flex-col gap-3">
				<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
					<OptionSelect
						aria-label="Persona"
						size="sm"
						value={filters.owner}
						onChange={(value) => updateFilter('owner', value ?? ALL)}
						options={owners.options}
					/>
					<OptionSelect
						aria-label="Tipo de evento"
						size="sm"
						value={filters.eventType}
						onChange={(value) => updateFilter('eventType', value ?? ALL)}
						options={EVENT_TYPE_FILTER_OPTIONS}
					/>
					<OptionSelect
						aria-label="Tipo de acción"
						size="sm"
						value={filters.kind}
						onChange={(value) => updateFilter('kind', value ?? ALL)}
						options={KIND_FILTER_OPTIONS}
					/>
					<OptionSelect
						aria-label="Resultado"
						size="sm"
						value={filters.result}
						onChange={(value) => updateFilter('result', value ?? ALL)}
						options={RESULT_FILTER_OPTIONS}
					/>
				</div>
				<div className="grid items-end gap-3 sm:grid-cols-2 lg:grid-cols-4">
					<Field className="lg:col-span-2">
						<FieldLabel htmlFor="audit-path">Ruta</FieldLabel>
						<div className="relative">
							<IconSearch className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
							<Input
								id="audit-path"
								placeholder="Busca en la ruta: /orders, /bots/12"
								value={path}
								maxLength={200}
								onChange={(event) => {
									setPath(event.target.value);
									setPage(1);
								}}
								className="h-10 pl-9"
							/>
						</div>
					</Field>
					<Field>
						<FieldLabel htmlFor="audit-date-from">Desde</FieldLabel>
						<Input
							id="audit-date-from"
							type="date"
							value={filters.dateFrom}
							max={filters.dateTo || undefined}
							onChange={(event) => updateFilter('dateFrom', event.target.value)}
							className="h-10"
						/>
					</Field>
					<Field>
						<FieldLabel htmlFor="audit-date-to">Hasta</FieldLabel>
						<Input
							id="audit-date-to"
							type="date"
							value={filters.dateTo}
							min={filters.dateFrom || undefined}
							aria-invalid={rangeInvalid || undefined}
							onChange={(event) => updateFilter('dateTo', event.target.value)}
							className="h-10"
						/>
					</Field>
				</div>
				{rangeInvalid && (
					<p className="text-sm text-destructive">
						La fecha final debe ser igual o posterior a la inicial.
					</p>
				)}
				{!filters.dateFrom && (
					<p className="text-xs text-muted-foreground">
						Sin fecha inicial se muestran este año y el anterior.
					</p>
				)}
			</div>
			<DataTable
				columns={columns}
				rows={data?.items ?? (rangeInvalid ? [] : undefined)}
				getRowId={(row) => row.key}
				isLoading={!rangeInvalid && eventsQuery.isLoading}
				error={rangeInvalid ? undefined : eventsQuery.error}
				errorTitle="No pudimos cargar la auditoría"
				onRowClick={setSelected}
				// La API ya devuelve una sola página: la paginación va abajo.
				paginate={false}
				empty={
					rangeInvalid
						? 'Corrige el rango de fechas para ver los eventos.'
						: hasFilters
							? 'No hay eventos con esos filtros.'
							: 'Aún no hay eventos registrados.'
				}
			/>
			{data && data.pagination.total > 0 && (
				<TablePagination
					page={data.pagination.page}
					limit={limit}
					total={data.pagination.total}
					totalPages={data.pagination.total_pages}
					onPageChange={setPage}
					onLimitChange={(next) => {
						setLimit(next);
						setPage(1);
					}}
				/>
			)}
			<AuditEventSheet
				event={selected}
				users={owners.byId}
				onClose={() => setSelected(null)}
			/>
		</div>
	);
}
