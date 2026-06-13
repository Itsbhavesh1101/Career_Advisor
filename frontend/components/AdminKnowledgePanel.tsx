"use client";

import { CheckCircle2, FileUp, Power, RefreshCw, XCircle } from "lucide-react";
import { useCallback, useEffect, useId, useMemo, useState } from "react";
import {
	buttonClass,
	CompactActionList,
	DataTable,
	Field,
	fieldControlClass,
	GlassPanel,
	Notice,
	ScoreBar,
	StatusBadge,
	Tag,
	Toolbar,
} from "@/components/ui";
import {
	createRagSource,
	listRagSources,
	type RAGDocumentSourceRead,
	type RAGReviewStatus,
	type RAGSourceStatus,
	type RAGSourceType,
	updateRagSourceReview,
	updateRagSourceStatus,
	uploadRagSourceFile,
} from "@/lib/api";
import { useBranding } from "@/lib/branding";

const SOURCE_TYPES: RAGSourceType[] = [
	"program",
	"counseling",
	"placement",
	"skill",
	"resume",
	"training",
	"policy",
];

type SafeSource = {
	id: number;
	title: string;
	sourceType: string;
	status: RAGSourceStatus;
	reviewStatus: RAGReviewStatus;
	freshnessStatus: string;
	reviewNotes: string | null;
	expiresAt: string | null;
	tags: string[];
	programIds: string[];
	chunkCount: number;
	updatedAt: string;
};

function splitCsv(value: string): string[] {
	const seen = new Set<string>();
	return value
		.split(",")
		.map((item) => item.trim())
		.filter(Boolean)
		.filter((item) => {
			const key = item.toLowerCase();
			if (seen.has(key)) return false;
			seen.add(key);
			return true;
		})
		.slice(0, 30);
}

function asStringArray(value: unknown): string[] {
	return Array.isArray(value)
		? value
				.filter((item): item is string => typeof item === "string")
				.map((item) => item.trim())
				.filter(Boolean)
				.slice(0, 30)
		: [];
}

function normalizeSource(source: RAGDocumentSourceRead): SafeSource | null {
	const id = Number(source.id);
	if (!Number.isInteger(id) || id <= 0) return null;

	return {
		id,
		title: source.title?.trim() || `Knowledge source #${id}`,
		sourceType: source.source_type?.trim() || "unknown",
		status: source.status === "inactive" ? "inactive" : "active",
		reviewStatus: source.review_status ?? "pending_review",
		freshnessStatus: source.freshness_status ?? "current",
		reviewNotes: source.review_notes ?? null,
		expiresAt: source.expires_at ?? null,
		tags: asStringArray(source.tags),
		programIds: asStringArray(source.program_ids),
		chunkCount: Math.max(0, Math.round(Number(source.chunk_count) || 0)),
		updatedAt: source.updated_at ?? "",
	};
}

function formatDate(value: string | null): string {
	if (!value) return "Not set";
	const parsed = new Date(value);
	if (Number.isNaN(parsed.getTime())) return "Not set";
	return parsed.toLocaleDateString(undefined, {
		month: "short",
		day: "numeric",
		year: "numeric",
	});
}

function reviewTone(
	status: RAGReviewStatus,
	freshnessStatus: string,
): "success" | "warning" | "danger" {
	if (freshnessStatus === "expired") return "warning";
	if (status === "approved") return "success";
	if (status === "rejected") return "danger";
	return "warning";
}

export default function AdminKnowledgePanel() {
	const branding = useBranding();
	const titleId = useId();
	const sourceTypeId = useId();
	const tagsId = useId();
	const programIdsId = useId();
	const sourceTextId = useId();
	const uploadFileId = useId();
	const [sources, setSources] = useState<SafeSource[]>([]);
	const [title, setTitle] = useState("");
	const [sourceType, setSourceType] = useState<RAGSourceType>("program");
	const [tagsInput, setTagsInput] = useState("");
	const [programIdsInput, setProgramIdsInput] = useState("");
	const [text, setText] = useState("");
	const [uploadFile, setUploadFile] = useState<File | null>(null);
	const [fileInputKey, setFileInputKey] = useState(0);
	const [loading, setLoading] = useState(true);
	const [saving, setSaving] = useState(false);
	const [uploading, setUploading] = useState(false);
	const [updatingId, setUpdatingId] = useState<number | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [notice, setNotice] = useState<string | null>(null);

	const tags = useMemo(() => splitCsv(tagsInput), [tagsInput]);
	const programIds = useMemo(
		() => splitCsv(programIdsInput),
		[programIdsInput],
	);
	const hasValidTitle = title.trim().length >= 3;
	const canCreate =
		hasValidTitle && text.trim().length >= 40 && !saving && !uploading;
	const sourceTitlePlaceholder =
		branding.mode === "sage" ? "SAGE AIML handbook" : "Program handbook";
	const canUpload =
		hasValidTitle && uploadFile !== null && !saving && !uploading;

	const reviewCounts = useMemo(
		() => ({
			pending: sources.filter(
				(source) => source.reviewStatus === "pending_review",
			).length,
			approved: sources.filter((source) => source.reviewStatus === "approved")
				.length,
			expired: sources.filter((source) => source.freshnessStatus === "expired")
				.length,
		}),
		[sources],
	);

	const loadSources = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const data = await listRagSources();
			const safeItems = Array.isArray(data?.items)
				? data.items
						.map(normalizeSource)
						.filter((item): item is SafeSource => Boolean(item))
				: [];
			setSources(safeItems);
		} catch (err) {
			setError(
				err instanceof Error ? err.message : "Failed to load knowledge.",
			);
			setSources([]);
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		void loadSources();
	}, [loadSources]);

	async function handleCreate() {
		if (!canCreate) {
			setError("Add a title and at least 40 characters of source text.");
			return;
		}
		setSaving(true);
		setError(null);
		setNotice(null);
		try {
			await createRagSource({
				title: title.trim(),
				source_type: sourceType,
				tags,
				program_ids: programIds,
				text: text.trim(),
			});
			setTitle("");
			setTagsInput("");
			setProgramIdsInput("");
			setText("");
			setNotice("Knowledge source created and queued for review.");
			await loadSources();
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to create source.");
		} finally {
			setSaving(false);
		}
	}

	async function handleUpload() {
		if (!uploadFile || !hasValidTitle) {
			setError("Add a title and choose a PDF or DOCX file.");
			return;
		}
		setUploading(true);
		setError(null);
		setNotice(null);
		try {
			await uploadRagSourceFile({
				title: title.trim(),
				source_type: sourceType,
				tags,
				program_ids: programIds,
				file: uploadFile,
			});
			setTitle("");
			setTagsInput("");
			setProgramIdsInput("");
			setUploadFile(null);
			setFileInputKey((current) => current + 1);
			setNotice("Knowledge file uploaded and queued for review.");
			await loadSources();
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to upload file.");
		} finally {
			setUploading(false);
		}
	}

	async function handleStatusChange(source: SafeSource) {
		const nextStatus: RAGSourceStatus =
			source.status === "active" ? "inactive" : "active";
		setUpdatingId(source.id);
		setError(null);
		setNotice(null);
		try {
			const updated = await updateRagSourceStatus(source.id, nextStatus);
			const normalized = normalizeSource(updated);
			setSources((current) =>
				current.map((item) =>
					item.id === source.id && normalized ? normalized : item,
				),
			);
			setNotice(`Source ${nextStatus === "active" ? "activated" : "paused"}.`);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to update status.");
		} finally {
			setUpdatingId(null);
		}
	}

	async function handleReviewChange(
		source: SafeSource,
		reviewStatus: RAGReviewStatus,
	) {
		setUpdatingId(source.id);
		setError(null);
		setNotice(null);
		try {
			const updated = await updateRagSourceReview(source.id, {
				review_status: reviewStatus,
				review_notes:
					reviewStatus === "approved"
						? "Approved for institutional guidance."
						: "Rejected from retrieval until updated.",
			});
			const normalized = normalizeSource(updated);
			setSources((current) =>
				current.map((item) =>
					item.id === source.id && normalized ? normalized : item,
				),
			);
			setNotice(`Source ${reviewStatus.replace("_", " ")}.`);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to update review.");
		} finally {
			setUpdatingId(null);
		}
	}

	return (
		<div className="space-y-5">
			<div className="flex flex-wrap items-start justify-between gap-3">
				<div>
					<h2 className="text-2xl font-semibold text-zinc-950">
						Knowledge governance
					</h2>
					<p className="mt-1 text-sm leading-6 text-zinc-600">
						Upload, review, and keep RAG sources trusted before they influence
						guidance.
					</p>
				</div>
				<button
					type="button"
					onClick={() => void loadSources()}
					disabled={loading}
					className={buttonClass({ variant: "secondary" })}
				>
					<RefreshCw
						className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`}
					/>
					Refresh
				</button>
			</div>

			<div className="grid gap-4 md:grid-cols-3">
				<GlassPanel as="div" className="p-4">
					<p className="text-sm font-medium text-zinc-600">Pending review</p>
					<p className="mt-2 text-3xl font-semibold text-zinc-950">
						{reviewCounts.pending}
					</p>
				</GlassPanel>
				<GlassPanel as="div" className="p-4">
					<p className="text-sm font-medium text-zinc-600">Approved sources</p>
					<p className="mt-2 text-3xl font-semibold text-zinc-950">
						{reviewCounts.approved}
					</p>
				</GlassPanel>
				<GlassPanel as="div" className="p-4">
					<p className="text-sm font-medium text-zinc-600">Expired/stale</p>
					<p className="mt-2 text-3xl font-semibold text-zinc-950">
						{reviewCounts.expired}
					</p>
				</GlassPanel>
			</div>

			{error ? (
				<Notice
					title="Knowledge action failed"
					description={error}
					tone="danger"
				/>
			) : null}
			{notice ? <Notice title={notice} tone="success" /> : null}

			<GlassPanel className="p-5">
				<div className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
					<div className="space-y-4">
						<div className="grid gap-3 sm:grid-cols-2">
							<Field label="Title" htmlFor={titleId}>
								<input
									id={titleId}
									value={title}
									onChange={(event) => setTitle(event.target.value)}
									maxLength={220}
									className={fieldControlClass}
									placeholder={sourceTitlePlaceholder}
								/>
							</Field>
							<Field label="Source type" htmlFor={sourceTypeId}>
								<select
									id={sourceTypeId}
									value={sourceType}
									onChange={(event) =>
										setSourceType(event.target.value as RAGSourceType)
									}
									className={fieldControlClass}
								>
									{SOURCE_TYPES.map((type) => (
										<option key={type} value={type}>
											{type}
										</option>
									))}
								</select>
							</Field>
						</div>
						<div className="grid gap-3 sm:grid-cols-2">
							<Field label="Tags" htmlFor={tagsId}>
								<input
									id={tagsId}
									value={tagsInput}
									onChange={(event) => setTagsInput(event.target.value)}
									className={fieldControlClass}
									placeholder="aiml, placement"
								/>
							</Field>
							<Field label="Program IDs" htmlFor={programIdsId}>
								<input
									id={programIdsId}
									value={programIdsInput}
									onChange={(event) => setProgramIdsInput(event.target.value)}
									className={fieldControlClass}
									placeholder="btech-aiml"
								/>
							</Field>
						</div>
						<Field label="Paste source text" htmlFor={sourceTextId}>
							<textarea
								id={sourceTextId}
								value={text}
								onChange={(event) => setText(event.target.value)}
								maxLength={20000}
								rows={7}
								className={`${fieldControlClass} resize-y`}
								placeholder="Paste counseling, placement, program, policy, or training guidance."
							/>
						</Field>
						<Toolbar className="justify-between">
							<p className="text-xs text-zinc-500">
								{text.trim().length}/20000 chars, {tags.length} tags,{" "}
								{programIds.length} programs
							</p>
							<button
								type="button"
								onClick={() => void handleCreate()}
								disabled={!canCreate}
								className={buttonClass()}
							>
								{saving ? "Creating..." : "Create source"}
							</button>
						</Toolbar>
					</div>

					<div className="space-y-4">
						<Notice
							title="Approved sources affect retrieval"
							description="New uploads stay pending until an admin approves them. Rejected or expired sources should not influence analysis evidence."
							tone="orange"
						/>
						<GlassPanel as="div" className="p-4">
							<Field
								label="PDF/DOCX file"
								htmlFor={uploadFileId}
								helper="Use this for institutional handbooks, placement notes, and policy documents."
							>
								<input
									id={uploadFileId}
									key={fileInputKey}
									type="file"
									accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
									onChange={(event) =>
										setUploadFile(event.target.files?.[0] ?? null)
									}
									className="block w-full rounded-lg border border-black/10 bg-white px-3 py-2 text-sm text-zinc-700 file:mr-3 file:rounded-full file:border-0 file:bg-zinc-950 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-white"
								/>
							</Field>
							<div className="mt-4 flex flex-wrap items-center justify-between gap-3">
								<p className="text-sm text-zinc-500">
									{uploadFile ? uploadFile.name : "No file selected"}
								</p>
								<button
									type="button"
									onClick={() => void handleUpload()}
									disabled={!canUpload}
									className={buttonClass({ variant: "dark" })}
								>
									<FileUp className="mr-2 h-4 w-4" />
									{uploading ? "Uploading..." : "Upload for review"}
								</button>
							</div>
						</GlassPanel>
					</div>
				</div>
			</GlassPanel>

			<DataTable>
				<thead className="border-b border-black/10 text-xs font-semibold text-zinc-500">
					<tr>
						<th className="px-4 py-3">Source</th>
						<th className="px-4 py-3">Trust</th>
						<th className="px-4 py-3">Coverage</th>
						<th className="px-4 py-3">Actions</th>
					</tr>
				</thead>
				<tbody>
					{sources.map((source) => {
						const disabled = updatingId === source.id;
						return (
							<tr
								key={source.id}
								className="border-b border-black/5 align-top last:border-0"
							>
								<td className="px-4 py-4">
									<p className="font-semibold text-zinc-950">{source.title}</p>
									<div className="mt-2 flex flex-wrap gap-2">
										<Tag>{source.sourceType}</Tag>
										<Tag
											tone={source.status === "active" ? "success" : "neutral"}
										>
											{source.status}
										</Tag>
									</div>
									<p className="mt-2 text-xs text-zinc-500">
										Updated {formatDate(source.updatedAt)}
									</p>
								</td>
								<td className="px-4 py-4">
									<StatusBadge
										tone={reviewTone(
											source.reviewStatus,
											source.freshnessStatus,
										)}
									>
										{source.freshnessStatus === "expired"
											? "expired"
											: source.reviewStatus.replace("_", " ")}
									</StatusBadge>
									<p className="mt-2 text-xs text-zinc-500">
										Expires {formatDate(source.expiresAt)}
									</p>
									{source.reviewNotes ? (
										<p className="mt-2 max-w-xs text-xs text-zinc-600">
											{source.reviewNotes}
										</p>
									) : null}
								</td>
								<td className="px-4 py-4">
									<ScoreBar value={Math.min(source.chunkCount * 10, 100)} />
									<p className="mt-2 text-sm text-zinc-700">
										{source.chunkCount} chunks
									</p>
									<div className="mt-2 flex max-w-sm flex-wrap gap-1.5">
										{source.tags.slice(0, 5).map((tag) => (
											<Tag key={tag}>{tag}</Tag>
										))}
									</div>
								</td>
								<td className="px-4 py-4">
									<div className="flex flex-wrap gap-2">
										<button
											type="button"
											disabled={disabled}
											onClick={() =>
												void handleReviewChange(source, "approved")
											}
											className={buttonClass({
												variant: "secondary",
												className: "min-h-8 px-3 py-1 text-xs",
											})}
										>
											<CheckCircle2 className="mr-1.5 h-3.5 w-3.5" />
											Approve
										</button>
										<button
											type="button"
											disabled={disabled}
											onClick={() =>
												void handleReviewChange(source, "rejected")
											}
											className={buttonClass({
												variant: "secondary",
												className: "min-h-8 px-3 py-1 text-xs",
											})}
										>
											<XCircle className="mr-1.5 h-3.5 w-3.5" />
											Reject
										</button>
										<button
											type="button"
											disabled={disabled}
											onClick={() => void handleStatusChange(source)}
											className={buttonClass({
												variant: "ghost",
												className: "min-h-8 px-3 py-1 text-xs",
											})}
										>
											<Power className="mr-1.5 h-3.5 w-3.5" />
											{source.status === "active" ? "Pause" : "Activate"}
										</button>
									</div>
								</td>
							</tr>
						);
					})}
					{!loading && sources.length === 0 ? (
						<tr>
							<td className="px-4 py-8 text-sm text-zinc-500" colSpan={4}>
								No knowledge sources yet.
							</td>
						</tr>
					) : null}
					{loading ? (
						<tr>
							<td className="px-4 py-8 text-sm text-zinc-500" colSpan={4}>
								Loading knowledge sources...
							</td>
						</tr>
					) : null}
				</tbody>
			</DataTable>
			<GlassPanel as="div" className="p-4">
				<p className="text-sm font-semibold text-zinc-950">Review checklist</p>
				<div className="mt-3">
					<CompactActionList
						items={[
							"Confirm the document is institution-approved.",
							"Check source type and program tags before approving.",
							"Reject stale or duplicate sources instead of pausing only.",
						]}
					/>
				</div>
			</GlassPanel>
		</div>
	);
}
