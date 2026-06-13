"use client";

import Link from "next/link";
import type { FormEvent } from "react";
import { useEffect, useId, useMemo, useState } from "react";
import AdminKnowledgePanel from "@/components/AdminKnowledgePanel";
import AdmissionIntelligencePanel from "@/components/AdmissionIntelligencePanel";
import PlacementIntelligencePanel from "@/components/PlacementIntelligencePanel";
import PlacementOpportunitiesPanel from "@/components/PlacementOpportunitiesPanel";
import {
	buttonClass,
	DataTable,
	EmptyState,
	Field,
	FormSection,
	fieldControlClass,
	GlassPanel,
	MetricTile,
	PageHeader,
	SectionTabs,
	StatusBadge,
} from "@/components/ui";
import {
	buildManagedItemDetailSummary,
	getManagedItemTypeConfig,
	getPayloadTemplate,
	managedItemTypeConfigs,
} from "@/lib/adminManagementUi";
import {
	type AdminManagedItemCreate,
	type AdminManagedItemRead,
	type AdminManagedItemType,
	type AdminManagedItemUpdate,
	type AdminMetricsRead,
	type AdminReadinessSummaryRead,
	type AdminSmokeDataCleanupPreviewRead,
	type AdminStudentRead,
	archiveAdminManagedItem,
	cleanupAdminSmokeData,
	createAdminManagedItem,
	getAdminMetrics,
	getAdminReadinessSummary,
	getAdminSmokeDataCleanupPreview,
	getAdminStudentsExportUrl,
	listAdminManagedItems,
	listAdminStudents,
	updateAdminManagedItem,
} from "@/lib/api";

type AdminTab =
	| "overview"
	| "management"
	| "admissions"
	| "placements"
	| "knowledge"
	| "students"
	| "maintenance";

const tabs: Array<{ id: AdminTab; label: string }> = [
	{ id: "overview", label: "Overview" },
	{ id: "management", label: "Management" },
	{ id: "admissions", label: "Admissions" },
	{ id: "placements", label: "Placements" },
	{ id: "knowledge", label: "Knowledge" },
	{ id: "students", label: "Students" },
	{ id: "maintenance", label: "Maintenance" },
];

const smokeCleanupConfirmation = "DELETE_SMOKE_TEST_DEMO_DATA";

export default function AdminDashboardPage() {
	const [activeTab, setActiveTab] = useState<AdminTab>("overview");
	const [metrics, setMetrics] = useState<AdminMetricsRead | null>(null);
	const [readiness, setReadiness] = useState<AdminReadinessSummaryRead | null>(
		null,
	);
	const [cleanupPreview, setCleanupPreview] =
		useState<AdminSmokeDataCleanupPreviewRead | null>(null);
	const [cleanupConfirm, setCleanupConfirm] = useState("");
	const [cleanupWorking, setCleanupWorking] = useState(false);
	const [cleanupMessage, setCleanupMessage] = useState<string | null>(null);
	const [managedItems, setManagedItems] = useState<AdminManagedItemRead[]>([]);
	const [managementMessage, setManagementMessage] = useState<string | null>(
		null,
	);
	const [students, setStudents] = useState<AdminStudentRead[]>([]);
	const [page, setPage] = useState(1);
	const [studentType, setStudentType] = useState("");
	const [readinessBand, setReadinessBand] = useState("");
	const [missingResume, setMissingResume] = useState(false);
	const [missingAnalysis, setMissingAnalysis] = useState(false);
	const [totalPages, setTotalPages] = useState(1);
	const [totalStudents, setTotalStudents] = useState(0);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		function applyHash() {
			const hash = window.location.hash.replace("#", "");
			if (tabs.some((tab) => tab.id === hash)) {
				setActiveTab(hash as AdminTab);
			}
		}

		applyHash();
		window.addEventListener("hashchange", applyHash);
		return () => window.removeEventListener("hashchange", applyHash);
	}, []);

	function updateActiveTab(tab: AdminTab) {
		setActiveTab(tab);
		if (tab === "overview") {
			window.history.replaceState(null, "", window.location.pathname);
			return;
		}
		window.history.replaceState(null, "", `#${tab}`);
	}

	useEffect(() => {
		let mounted = true;
		async function load() {
			setLoading(true);
			setError(null);
			try {
				const [
					metricsData,
					summaryData,
					cleanupData,
					managementData,
					studentsData,
				] = await Promise.all([
					getAdminMetrics(),
					getAdminReadinessSummary(),
					getAdminSmokeDataCleanupPreview(),
					listAdminManagedItems(),
					listAdminStudents(page, 25, {
						student_type: studentType,
						readiness_band: readinessBand,
						missing_resume: missingResume || undefined,
						missing_analysis: missingAnalysis || undefined,
					}),
				]);
				if (!mounted) return;
				setMetrics(metricsData);
				setReadiness(summaryData);
				setCleanupPreview(cleanupData);
				setManagedItems(managementData.items);
				setStudents(studentsData.items);
				setTotalPages(studentsData.total_pages);
				setTotalStudents(studentsData.total);
			} catch (err) {
				if (mounted) {
					setError(
						err instanceof Error ? err.message : "Failed to load admin data.",
					);
				}
			} finally {
				if (mounted) setLoading(false);
			}
		}
		void load();
		return () => {
			mounted = false;
		};
	}, [page, studentType, readinessBand, missingResume, missingAnalysis]);

	async function runSmokeCleanup() {
		setCleanupWorking(true);
		setCleanupMessage(null);
		try {
			const result = await cleanupAdminSmokeData(cleanupConfirm);
			const [metricsData, summaryData, cleanupData, studentsData] =
				await Promise.all([
					getAdminMetrics(),
					getAdminReadinessSummary(),
					getAdminSmokeDataCleanupPreview(),
					listAdminStudents(page, 25, {
						student_type: studentType,
						readiness_band: readinessBand,
						missing_resume: missingResume || undefined,
						missing_analysis: missingAnalysis || undefined,
					}),
				]);
			setMetrics(metricsData);
			setReadiness(summaryData);
			setCleanupPreview(cleanupData);
			setStudents(studentsData.items);
			setTotalPages(studentsData.total_pages);
			setTotalStudents(studentsData.total);
			setCleanupConfirm("");
			setCleanupMessage(
				result.deleted
					? "Smoke/test/demo data cleanup completed."
					: "No eligible smoke/test/demo data was found.",
			);
		} catch (err) {
			setCleanupMessage(
				err instanceof Error ? err.message : "Smoke data cleanup failed.",
			);
		} finally {
			setCleanupWorking(false);
		}
	}

	async function reloadManagementItems() {
		const data = await listAdminManagedItems();
		setManagedItems(data.items);
	}

	async function handleCreateManagedItem(payload: AdminManagedItemCreate) {
		setManagementMessage(null);
		try {
			await createAdminManagedItem(payload);
			await reloadManagementItems();
			setManagementMessage("Management item saved.");
		} catch (err) {
			setManagementMessage(
				err instanceof Error ? err.message : "Management item could not save.",
			);
			throw err;
		}
	}

	async function handleUpdateManagedItem(
		itemId: number,
		payload: AdminManagedItemUpdate,
	) {
		setManagementMessage(null);
		try {
			await updateAdminManagedItem(itemId, payload);
			await reloadManagementItems();
			setManagementMessage("Management item updated.");
		} catch (err) {
			setManagementMessage(
				err instanceof Error
					? err.message
					: "Management item could not update.",
			);
			throw err;
		}
	}

	async function handleArchiveManagedItem(itemId: number) {
		setManagementMessage(null);
		try {
			await archiveAdminManagedItem(itemId);
			await reloadManagementItems();
			setManagementMessage("Management item archived.");
		} catch (err) {
			setManagementMessage(
				err instanceof Error
					? err.message
					: "Management item could not archive.",
			);
			throw err;
		}
	}

	const exportHref = getAdminStudentsExportUrl({
		student_type: studentType,
		readiness_band: readinessBand,
		missing_resume: missingResume || undefined,
		missing_analysis: missingAnalysis || undefined,
	});

	const criticalCount = useMemo(() => {
		if (!readiness && !metrics) return 0;
		return (
			(readiness?.failed_analysis_jobs ?? 0) +
			(readiness?.pending_rag_reviews ?? 0) +
			(readiness?.stale_rag_sources ?? 0) +
			(readiness?.missing_analysis ?? 0) +
			(metrics?.high_risk ?? 0)
		);
	}, [readiness, metrics]);

	return (
		<main className="mx-auto max-w-6xl space-y-5 px-5 py-6 sm:px-6 lg:py-8">
			<PageHeader
				title="Institution command center"
				description="Launch readiness, admissions, placements, trusted knowledge, and student action queues without a CRM/ATS layer."
				actions={
					<Link
						href="/dashboard"
						className={buttonClass({ variant: "secondary" })}
					>
						Student view
					</Link>
				}
			/>

			{error ? (
				<EmptyState title="Admin data could not load" description={error} />
			) : null}

			<SectionTabs
				items={tabs.map((tab) => ({
					...tab,
					count: tab.id === "overview" ? criticalCount : undefined,
				}))}
				active={activeTab}
				onChange={updateActiveTab}
			/>

			{loading ? (
				<GlassPanel>
					<p className="text-sm text-zinc-600">Loading command center...</p>
				</GlassPanel>
			) : null}

			{activeTab === "overview" ? (
				<OverviewPanel
					metrics={metrics}
					readiness={readiness}
					onOpenStudents={() => updateActiveTab("students")}
					onOpenKnowledge={() => updateActiveTab("knowledge")}
					onOpenManagement={() => updateActiveTab("management")}
				/>
			) : null}

			{activeTab === "management" ? (
				<ManagementPanel
					items={managedItems}
					message={managementMessage}
					onCreate={handleCreateManagedItem}
					onUpdate={handleUpdateManagedItem}
					onArchive={handleArchiveManagedItem}
				/>
			) : null}
			{activeTab === "admissions" ? <AdmissionIntelligencePanel /> : null}
			{activeTab === "placements" ? (
				<div className="space-y-5">
					<PlacementOpportunitiesPanel />
					<PlacementIntelligencePanel />
				</div>
			) : null}
			{activeTab === "knowledge" ? <AdminKnowledgePanel /> : null}
			{activeTab === "students" ? (
				<StudentsPanel
					students={students}
					page={page}
					totalPages={totalPages}
					totalStudents={totalStudents}
					studentType={studentType}
					readinessBand={readinessBand}
					missingResume={missingResume}
					missingAnalysis={missingAnalysis}
					exportHref={exportHref}
					setPage={setPage}
					setStudentType={setStudentType}
					setReadinessBand={setReadinessBand}
					setMissingResume={setMissingResume}
					setMissingAnalysis={setMissingAnalysis}
				/>
			) : null}
			{activeTab === "maintenance" ? (
				<MaintenancePanel
					preview={cleanupPreview}
					confirm={cleanupConfirm}
					working={cleanupWorking}
					message={cleanupMessage}
					setConfirm={setCleanupConfirm}
					onCleanup={runSmokeCleanup}
				/>
			) : null}
		</main>
	);
}

function OverviewPanel({
	metrics,
	readiness,
	onOpenStudents,
	onOpenKnowledge,
	onOpenManagement,
}: {
	metrics: AdminMetricsRead | null;
	readiness: AdminReadinessSummaryRead | null;
	onOpenStudents: () => void;
	onOpenKnowledge: () => void;
	onOpenManagement: () => void;
}) {
	return (
		<div className="space-y-5">
			<section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
				<MetricTile
					label="Failed jobs"
					value={readiness?.failed_analysis_jobs ?? 0}
					helper="Analysis recovery queue"
					tone={
						(readiness?.failed_analysis_jobs ?? 0) > 0 ? "danger" : "success"
					}
				/>
				<MetricTile
					label="Pending RAG"
					value={readiness?.pending_rag_reviews ?? 0}
					helper="Knowledge awaiting review"
					tone={
						(readiness?.pending_rag_reviews ?? 0) > 0 ? "warning" : "success"
					}
				/>
				<MetricTile
					label="Missing analysis"
					value={readiness?.missing_analysis ?? 0}
					helper="Students needing AI output"
					tone={(readiness?.missing_analysis ?? 0) > 0 ? "warning" : "success"}
				/>
				<MetricTile
					label="High risk"
					value={metrics?.high_risk ?? 0}
					helper="Placement intervention"
					tone={(metrics?.high_risk ?? 0) > 0 ? "danger" : "success"}
				/>
			</section>

			<section className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
				<GlassPanel tone="orange" className="p-6">
					<div className="flex flex-wrap items-start justify-between gap-4">
						<div>
							<h2 className="text-2xl font-semibold tracking-tight text-zinc-950">
								Institution operations
							</h2>
							<p className="mt-2 max-w-xl text-sm leading-6 text-zinc-700">
								Keep student queues, knowledge reviews, programs, training,
								internships, and placement partners aligned from one admin
								workspace.
							</p>
						</div>
						<StatusBadge tone={criticalTone(readiness, metrics)}>
							{(readiness?.failed_analysis_jobs ?? 0) +
								(readiness?.pending_rag_reviews ?? 0) +
								(readiness?.missing_analysis ?? 0) +
								(metrics?.high_risk ?? 0)}{" "}
							needs action
						</StatusBadge>
					</div>
					<div className="mt-6 grid gap-3 md:grid-cols-3">
						<ActionRow
							title="Manage institution catalog"
							description="Programs, training, internships, and placement companies"
							onClick={onOpenManagement}
						/>
						<ActionRow
							title="Review student queues"
							description={`${readiness?.missing_resume ?? 0} missing resumes, ${readiness?.missing_analysis ?? 0} missing analyses`}
							onClick={onOpenStudents}
						/>
						<ActionRow
							title="Review knowledge trust"
							description={`${readiness?.pending_rag_reviews ?? 0} pending, ${readiness?.stale_rag_sources ?? 0} stale`}
							onClick={onOpenKnowledge}
						/>
					</div>
				</GlassPanel>

				<GlassPanel className="p-6">
					<h2 className="text-xl font-semibold text-zinc-950">
						Next admin actions
					</h2>
					<div className="mt-5 space-y-3">
						<ActionRow
							title="Update managed catalog"
							description="Add or archive programs, training plans, internships, and companies"
							onClick={onOpenManagement}
						/>
						<ActionRow
							title="Review student action queues"
							description={`${readiness?.missing_resume ?? 0} missing resumes, ${readiness?.missing_analysis ?? 0} missing analyses`}
							onClick={onOpenStudents}
						/>
						<ActionRow
							title="Check knowledge trust"
							description={`${readiness?.pending_rag_reviews ?? 0} pending, ${readiness?.stale_rag_sources ?? 0} stale`}
							onClick={onOpenKnowledge}
						/>
					</div>
				</GlassPanel>
			</section>
		</div>
	);
}

function criticalTone(
	readiness: AdminReadinessSummaryRead | null,
	metrics: AdminMetricsRead | null,
): "warning" | "success" {
	const count =
		(readiness?.failed_analysis_jobs ?? 0) +
		(readiness?.pending_rag_reviews ?? 0) +
		(readiness?.missing_analysis ?? 0) +
		(metrics?.high_risk ?? 0);
	return count > 0 ? "warning" : "success";
}

function ActionRow({
	title,
	description,
	onClick,
}: {
	title: string;
	description: string;
	onClick: () => void;
}) {
	return (
		<button
			type="button"
			onClick={onClick}
			className="w-full rounded-lg border border-black/10 bg-white/60 p-4 text-left transition hover:border-orange-300 hover:bg-orange-50"
		>
			<p className="font-semibold text-zinc-950">{title}</p>
			<p className="mt-1 text-sm text-zinc-600">{description}</p>
		</button>
	);
}

function ManagementPanel({
	items,
	message,
	onCreate,
	onUpdate,
	onArchive,
}: {
	items: AdminManagedItemRead[];
	message: string | null;
	onCreate: (payload: AdminManagedItemCreate) => Promise<void>;
	onUpdate: (itemId: number, payload: AdminManagedItemUpdate) => Promise<void>;
	onArchive: (itemId: number) => Promise<void>;
}) {
	const typeId = useId();
	const slugId = useId();
	const titleId = useId();
	const summaryId = useId();
	const payloadId = useId();
	const [editingItem, setEditingItem] = useState<AdminManagedItemRead | null>(
		null,
	);
	const [itemType, setItemType] = useState<AdminManagedItemType>("program");
	const [visibleType, setVisibleType] = useState<AdminManagedItemType | "all">(
		"all",
	);
	const [slug, setSlug] = useState("");
	const [title, setTitle] = useState("");
	const [summary, setSummary] = useState("");
	const [payloadText, setPayloadText] = useState(() =>
		JSON.stringify(getPayloadTemplate("program"), null, 2),
	);
	const [localError, setLocalError] = useState<string | null>(null);
	const [saving, setSaving] = useState(false);

	function resetForm() {
		setEditingItem(null);
		setItemType("program");
		setSlug("");
		setTitle("");
		setSummary("");
		setPayloadText(JSON.stringify(getPayloadTemplate("program"), null, 2));
		setLocalError(null);
	}

	function startEdit(item: AdminManagedItemRead) {
		setEditingItem(item);
		setItemType(item.item_type);
		setSlug(item.slug);
		setTitle(item.title);
		setSummary(item.summary ?? "");
		setPayloadText(JSON.stringify(item.payload ?? {}, null, 2));
		setLocalError(null);
	}

	async function handleSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setLocalError(null);
		let parsedPayload: AdminManagedItemCreate["payload"];
		try {
			const parsed = JSON.parse(payloadText) as unknown;
			if (!isRecord(parsed)) {
				throw new Error("Payload must be a JSON object.");
			}
			parsedPayload = parsed as AdminManagedItemCreate["payload"];
		} catch (err) {
			setLocalError(
				err instanceof Error ? err.message : "Payload must be valid JSON.",
			);
			return;
		}

		setSaving(true);
		try {
			const basePayload = {
				slug,
				title,
				summary: summary.trim() || null,
				status: "active" as const,
				payload: parsedPayload,
			};
			if (editingItem) {
				await onUpdate(editingItem.id, basePayload);
			} else {
				await onCreate({ item_type: itemType, ...basePayload });
			}
			resetForm();
		} catch {
			// Parent handler sets the user-facing message.
		} finally {
			setSaving(false);
		}
	}

	const activeCount = items.filter((item) => item.status === "active").length;
	const visibleItems =
		visibleType === "all"
			? items
			: items.filter((item) => item.item_type === visibleType);

	return (
		<div className="space-y-5">
			<section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
				{managedItemTypeConfigs.map((type) => {
					const count = items.filter(
						(item) => item.item_type === type.value,
					).length;
					return (
						<MetricTile
							key={type.value}
							label={type.label}
							value={count}
							helper={type.helper}
							tone={count > 0 ? "orange" : "neutral"}
						/>
					);
				})}
			</section>

			<GlassPanel className="grid gap-5 p-6 lg:grid-cols-[0.86fr_1.14fr]">
				<div>
					<h2 className="text-2xl font-semibold text-zinc-950">
						Manage catalog and career operations
					</h2>
					<p className="mt-2 text-sm leading-6 text-zinc-600">
						Add institution-specific programs, training plans, internship
						opportunities, placement companies, policies, knowledge templates,
						and reusable content. Active programs extend the student program
						catalog, active training plans feed recommendations, and active
						internships appear in the student internship workspace.
					</p>
					<div className="mt-4 flex flex-wrap gap-2">
						<StatusBadge tone="orange">{activeCount} active</StatusBadge>
						<StatusBadge tone="neutral">{items.length} total</StatusBadge>
					</div>
					{message ? (
						<p className="mt-4 rounded-lg border border-black/10 bg-white px-3 py-2 text-sm font-medium text-zinc-700">
							{message}
						</p>
					) : null}
					{localError ? (
						<p className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-800">
							{localError}
						</p>
					) : null}
				</div>

				<form onSubmit={handleSubmit} className="space-y-4">
					<FormSection
						title={editingItem ? "Edit item" : "Add item"}
						description="Pick a type to start with a safe template. Advanced fields stay in structured JSON so this remains flexible without adding duplicate modules."
					>
						<div className="grid gap-3 md:grid-cols-2">
							<Field label="Type" htmlFor={typeId}>
								<select
									id={typeId}
									value={itemType}
									onChange={(event) => {
										const nextType = event.target.value as AdminManagedItemType;
										setItemType(nextType);
										if (!editingItem) {
											setPayloadText(
												JSON.stringify(getPayloadTemplate(nextType), null, 2),
											);
										}
									}}
									disabled={Boolean(editingItem)}
									className={fieldControlClass}
								>
									{managedItemTypeConfigs.map((type) => (
										<option key={type.value} value={type.value}>
											{type.label}
										</option>
									))}
								</select>
							</Field>
							<Field label="Slug" htmlFor={slugId}>
								<input
									id={slugId}
									value={slug}
									onChange={(event) => setSlug(event.target.value)}
									className={fieldControlClass}
									placeholder="btech-data-science"
									required
								/>
							</Field>
							<Field label="Title" htmlFor={titleId}>
								<input
									id={titleId}
									value={title}
									onChange={(event) => setTitle(event.target.value)}
									className={fieldControlClass}
									placeholder="B.Tech Data Science"
									required
								/>
							</Field>
							<Field label="Summary" htmlFor={summaryId}>
								<input
									id={summaryId}
									value={summary}
									onChange={(event) => setSummary(event.target.value)}
									className={fieldControlClass}
									placeholder="Short admin-facing description"
								/>
							</Field>
						</div>
						<Field label="Structured payload" htmlFor={payloadId}>
							<textarea
								id={payloadId}
								value={payloadText}
								onChange={(event) => setPayloadText(event.target.value)}
								className={`${fieldControlClass} min-h-32 font-mono`}
								spellCheck={false}
							/>
						</Field>
						<div className="rounded-xl border border-black/10 bg-white/70 p-3 text-xs leading-5 text-zinc-600">
							<p className="font-semibold text-zinc-800">
								{getManagedItemTypeConfig(itemType).label} template
							</p>
							<p className="mt-1">
								{getManagedItemTypeConfig(itemType).helper}
							</p>
						</div>
						<div className="flex flex-wrap gap-2">
							<button
								type="submit"
								disabled={saving}
								className={buttonClass({ variant: "primary" })}
							>
								{saving
									? "Saving..."
									: editingItem
										? "Update item"
										: "Add item"}
							</button>
							{editingItem ? (
								<button
									type="button"
									onClick={resetForm}
									className={buttonClass({ variant: "secondary" })}
								>
									Cancel edit
								</button>
							) : null}
						</div>
					</FormSection>
				</form>
			</GlassPanel>

			<GlassPanel className="space-y-4 p-6">
				<div className="flex flex-wrap items-center justify-between gap-3">
					<div>
						<h2 className="text-xl font-semibold text-zinc-950">
							Managed items
						</h2>
						<p className="mt-1 text-sm text-zinc-600">
							Archive an item to keep history while removing it from active
							student/admin use.
						</p>
					</div>
					<div className="flex flex-wrap gap-2">
						<button
							type="button"
							onClick={() => setVisibleType("all")}
							className={buttonClass({
								variant: visibleType === "all" ? "dark" : "secondary",
								className: "min-h-8 px-3 py-1 text-xs",
							})}
						>
							All
						</button>
						{managedItemTypeConfigs.map((type) => (
							<button
								type="button"
								key={type.value}
								onClick={() => setVisibleType(type.value)}
								className={buttonClass({
									variant: visibleType === type.value ? "dark" : "secondary",
									className: "min-h-8 px-3 py-1 text-xs",
								})}
							>
								{type.label}
							</button>
						))}
					</div>
				</div>
				<DataTable>
					<thead className="border-b border-black/10 text-xs font-semibold text-zinc-500">
						<tr>
							<th className="px-4 py-3">Type</th>
							<th className="px-4 py-3">Item</th>
							<th className="px-4 py-3">Status</th>
							<th className="px-4 py-3">Details</th>
							<th className="px-4 py-3">Actions</th>
						</tr>
					</thead>
					<tbody>
						{visibleItems.map((item) => (
							<tr
								key={item.id}
								className="border-b border-black/5 last:border-0"
							>
								<td className="px-4 py-3">
									{formatManagedItemType(item.item_type)}
								</td>
								<td className="px-4 py-3">
									<p className="font-semibold text-zinc-950">{item.title}</p>
									<p className="text-xs text-zinc-500">{item.slug}</p>
								</td>
								<td className="px-4 py-3">
									<StatusBadge
										tone={item.status === "active" ? "success" : "neutral"}
									>
										{item.status}
									</StatusBadge>
								</td>
								<td className="max-w-md px-4 py-3">
									<p className="font-medium text-zinc-800">
										{buildManagedItemDetailSummary(item)}
									</p>
									<p className="mt-1 text-xs text-zinc-500">
										{item.summary || "No summary yet."}
									</p>
								</td>
								<td className="px-4 py-3">
									<div className="flex flex-wrap gap-2">
										<button
											type="button"
											onClick={() => startEdit(item)}
											className={buttonClass({
												variant: "secondary",
												className: "min-h-8 px-3 py-1 text-xs",
											})}
										>
											Edit
										</button>
										<button
											type="button"
											onClick={() =>
												void onArchive(item.id).catch(() => undefined)
											}
											disabled={item.status === "inactive"}
											className={buttonClass({
												variant: "ghost",
												className: "min-h-8 px-3 py-1 text-xs",
											})}
										>
											Archive
										</button>
									</div>
								</td>
							</tr>
						))}
						{visibleItems.length === 0 ? (
							<tr>
								<td className="px-4 py-6 text-sm text-zinc-500" colSpan={5}>
									No managed items match this filter. Add programs, training
									plans, internships, companies, policies, knowledge templates,
									or institution content above.
								</td>
							</tr>
						) : null}
					</tbody>
				</DataTable>
			</GlassPanel>
		</div>
	);
}

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatManagedItemType(itemType: AdminManagedItemType) {
	return getManagedItemTypeConfig(itemType).label;
}

function StudentsPanel({
	students,
	page,
	totalPages,
	totalStudents,
	studentType,
	readinessBand,
	missingResume,
	missingAnalysis,
	exportHref,
	setPage,
	setStudentType,
	setReadinessBand,
	setMissingResume,
	setMissingAnalysis,
}: {
	students: AdminStudentRead[];
	page: number;
	totalPages: number;
	totalStudents: number;
	studentType: string;
	readinessBand: string;
	missingResume: boolean;
	missingAnalysis: boolean;
	exportHref: string;
	setPage: (value: number | ((current: number) => number)) => void;
	setStudentType: (value: string) => void;
	setReadinessBand: (value: string) => void;
	setMissingResume: (value: boolean) => void;
	setMissingAnalysis: (value: boolean) => void;
}) {
	return (
		<GlassPanel className="space-y-5 p-6">
			<div className="flex flex-wrap items-start justify-between gap-4">
				<div>
					<h2 className="text-2xl font-semibold text-zinc-950">Students</h2>
					<p className="mt-1 text-sm text-zinc-600">
						Page {page} of {totalPages} - {totalStudents} total profiles
					</p>
				</div>
				<div className="flex flex-wrap gap-2">
					<button
						type="button"
						onClick={() => setPage((current) => Math.max(1, current - 1))}
						disabled={page <= 1}
						className={buttonClass({ variant: "secondary" })}
					>
						Previous
					</button>
					<button
						type="button"
						onClick={() =>
							setPage((current) => Math.min(totalPages, current + 1))
						}
						disabled={page >= totalPages}
						className={buttonClass({ variant: "secondary" })}
					>
						Next
					</button>
					<a href={exportHref} className={buttonClass({ variant: "primary" })}>
						Export CSV
					</a>
				</div>
			</div>

			<div className="grid gap-3 rounded-xl border border-black/10 bg-white/60 p-3 md:grid-cols-5">
				<select
					value={studentType}
					onChange={(event) => {
						setPage(1);
						setStudentType(event.target.value);
					}}
					className="rounded-lg border border-black/10 bg-white px-3 py-2 text-sm text-zinc-950"
				>
					<option value="">All students</option>
					<option value="twelfth_student">12th students</option>
					<option value="college_student">College students</option>
				</select>
				<select
					value={readinessBand}
					onChange={(event) => {
						setPage(1);
						setReadinessBand(event.target.value);
					}}
					className="rounded-lg border border-black/10 bg-white px-3 py-2 text-sm text-zinc-950"
				>
					<option value="">All readiness</option>
					<option value="ready">Ready</option>
					<option value="watch">Watch</option>
					<option value="risk">Risk</option>
					<option value="unknown">Unknown</option>
				</select>
				<label className="inline-flex items-center gap-2 text-sm text-zinc-700">
					<input
						type="checkbox"
						checked={missingAnalysis}
						onChange={(event) => {
							setPage(1);
							setMissingAnalysis(event.target.checked);
						}}
					/>
					Missing analysis
				</label>
				<label className="inline-flex items-center gap-2 text-sm text-zinc-700">
					<input
						type="checkbox"
						checked={missingResume}
						onChange={(event) => {
							setPage(1);
							setMissingResume(event.target.checked);
						}}
					/>
					Missing resume
				</label>
			</div>

			<DataTable>
				<thead className="border-b border-black/10 text-xs font-semibold text-zinc-500">
					<tr>
						<th className="px-4 py-3">Name</th>
						<th className="px-4 py-3">Program</th>
						<th className="px-4 py-3">Employability</th>
						<th className="px-4 py-3">Risk</th>
						<th className="px-4 py-3">Status</th>
						<th className="px-4 py-3">Profile</th>
					</tr>
				</thead>
				<tbody>
					{students.map((student) => (
						<tr
							key={student.profile_id}
							className="border-b border-black/5 last:border-0"
						>
							<td className="px-4 py-3 font-semibold text-zinc-950">
								{student.name}
							</td>
							<td className="px-4 py-3">
								{student.degree || "-"}{" "}
								{student.specialization ? `- ${student.specialization}` : ""}
							</td>
							<td className="px-4 py-3">
								{student.employability_score ?? "-"}
							</td>
							<td className="px-4 py-3">{student.placement_risk ?? "-"}</td>
							<td className="px-4 py-3">
								<StatusBadge
									tone={
										student.readiness_band === "risk"
											? "danger"
											: student.readiness_band === "ready"
												? "success"
												: "warning"
									}
								>
									{student.readiness_band}
								</StatusBadge>
								<p className="mt-1 text-xs text-zinc-500">
									{student.has_analysis ? "Analysis ready" : "Needs analysis"} /{" "}
									{student.has_resume ? "Resume ready" : "No resume"}
								</p>
							</td>
							<td className="px-4 py-3">
								<Link
									className={buttonClass({
										variant: "ghost",
										className: "min-h-8 px-3 py-1 text-xs",
									})}
									href={`/analysis/${student.profile_id}`}
								>
									View
								</Link>
							</td>
						</tr>
					))}
					{students.length === 0 ? (
						<tr>
							<td className="px-4 py-6 text-sm text-zinc-500" colSpan={6}>
								No students match the current filters.
							</td>
						</tr>
					) : null}
				</tbody>
			</DataTable>
		</GlassPanel>
	);
}

function MaintenancePanel({
	preview,
	confirm,
	working,
	message,
	setConfirm,
	onCleanup,
}: {
	preview: AdminSmokeDataCleanupPreviewRead | null;
	confirm: string;
	working: boolean;
	message: string | null;
	setConfirm: (value: string) => void;
	onCleanup: () => void;
}) {
	const cleanupConfirmId = useId();
	const rows = [
		["Users", preview?.users ?? 0],
		["Profiles", preview?.profiles ?? 0],
		["Analysis jobs", preview?.analysis_jobs ?? 0],
		["Career analyses", preview?.career_analyses ?? 0],
		["Resume analyses", preview?.resume_analyses ?? 0],
		["Employability scores", preview?.employability_scores ?? 0],
		["Placement risks", preview?.placement_risks ?? 0],
		["Company fits", preview?.company_fits ?? 0],
		["Role gap analyses", preview?.role_gap_analyses ?? 0],
		["Internship readiness", preview?.internship_readiness ?? 0],
		["Quiz sessions", preview?.quiz_sessions ?? 0],
		["Quiz questions", preview?.quiz_questions ?? 0],
		["Quiz answers", preview?.quiz_answers ?? 0],
		["Quiz results", preview?.quiz_results ?? 0],
		["RAG sources", preview?.rag_sources ?? 0],
		["RAG chunks", preview?.rag_chunks ?? 0],
	] as const;
	const total = rows.reduce((sum, [, value]) => sum + value, 0);
	const canCleanup = confirm === smokeCleanupConfirmation && !working;

	return (
		<GlassPanel className="space-y-5 p-6">
			<div className="flex flex-wrap items-start justify-between gap-4">
				<div>
					<h2 className="text-2xl font-semibold text-zinc-950">
						Safe smoke data cleanup
					</h2>
					<p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
						Preview and remove only conservative smoke, test, and demo records.
						Regular student accounts and approved production knowledge remain
						outside this cleanup.
					</p>
				</div>
				<StatusBadge tone={total > 0 ? "warning" : "success"}>
					{total} eligible records
				</StatusBadge>
			</div>

			<div className="grid gap-4 lg:grid-cols-[1fr_0.78fr]">
				<DataTable>
					<thead className="border-b border-black/10 text-xs font-semibold text-zinc-500">
						<tr>
							<th className="px-4 py-3">Data type</th>
							<th className="px-4 py-3 text-right">Eligible</th>
						</tr>
					</thead>
					<tbody>
						{rows.map(([label, value]) => (
							<tr key={label} className="border-b border-black/5 last:border-0">
								<td className="px-4 py-3">{label}</td>
								<td className="px-4 py-3 text-right font-semibold text-zinc-950">
									{value}
								</td>
							</tr>
						))}
					</tbody>
				</DataTable>

				<div className="space-y-4 rounded-xl border border-black/10 bg-white/70 p-4">
					<div>
						<p className="text-sm font-semibold text-zinc-950">
							Sample matched accounts
						</p>
						{preview?.sample_emails.length ? (
							<ul className="mt-2 space-y-1 text-sm text-zinc-600">
								{preview.sample_emails.map((email) => (
									<li key={email}>{email}</li>
								))}
							</ul>
						) : (
							<p className="mt-2 text-sm text-zinc-500">No account matches.</p>
						)}
					</div>

					<div>
						<p className="text-sm font-semibold text-zinc-950">
							Sample matched knowledge
						</p>
						{preview?.sample_rag_titles.length ? (
							<ul className="mt-2 space-y-1 text-sm text-zinc-600">
								{preview.sample_rag_titles.map((title) => (
									<li key={title}>{title}</li>
								))}
							</ul>
						) : (
							<p className="mt-2 text-sm text-zinc-500">No source matches.</p>
						)}
					</div>
				</div>
			</div>

			<div className="rounded-xl border border-orange-200 bg-orange-50 p-4">
				<label
					htmlFor={cleanupConfirmId}
					className="text-sm font-semibold text-zinc-950"
				>
					Type confirmation phrase to run cleanup
				</label>
				<p className="mt-1 text-sm text-zinc-600">
					Required phrase:{" "}
					<span className="font-semibold text-zinc-950">
						{smokeCleanupConfirmation}
					</span>
				</p>
				<div className="mt-3 flex flex-col gap-3 sm:flex-row">
					<input
						id={cleanupConfirmId}
						value={confirm}
						onChange={(event) => setConfirm(event.target.value)}
						className="min-h-10 flex-1 rounded-lg border border-black/10 bg-white px-3 py-2 text-sm text-zinc-950 outline-none focus:border-orange-300 focus:ring-2 focus:ring-orange-200"
						placeholder={smokeCleanupConfirmation}
					/>
					<button
						type="button"
						onClick={onCleanup}
						disabled={!canCleanup}
						className={buttonClass({ variant: "dark" })}
					>
						{working ? "Cleaning..." : "Clean eligible data"}
					</button>
				</div>
				{message ? (
					<p className="mt-3 text-sm font-medium text-zinc-700">{message}</p>
				) : null}
			</div>
		</GlassPanel>
	);
}
