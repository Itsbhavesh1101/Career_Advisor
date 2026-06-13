import type {
	AgentStageSummary,
	AnalysisSnapshotSummary,
	SnapshotVerifierResult,
} from "@/lib/api";

type SafeStageStatus = AgentStageSummary["status"];

const statusTone: Record<SafeStageStatus, string> = {
	completed: "border-emerald-200 bg-emerald-50 text-emerald-800",
	skipped: "border-zinc-200 bg-zinc-50 text-zinc-600",
	failed: "border-red-200 bg-red-50 text-red-800",
};

function isRecord(value: unknown): value is Record<string, unknown> {
	return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function asString(value: unknown, fallback = ""): string {
	return typeof value === "string" && value.trim() ? value : fallback;
}

function asStringArray(value: unknown): string[] {
	if (!Array.isArray(value)) {
		return [];
	}

	return value.filter((item): item is string => typeof item === "string");
}

function asStatus(value: unknown): SafeStageStatus {
	return value === "completed" || value === "failed" || value === "skipped"
		? value
		: "skipped";
}

function normalizeStage(value: unknown): AgentStageSummary | null {
	if (!isRecord(value)) {
		return null;
	}

	const stage = asString(value.stage);
	if (!stage) {
		return null;
	}

	return {
		stage,
		label: asString(value.label, stage),
		status: asStatus(value.status),
		source: asString(value.source, "unknown"),
		output_ref:
			typeof value.output_ref === "string" || value.output_ref === null
				? value.output_ref
				: null,
		notes: asStringArray(value.notes),
	};
}

function isAgentStageSummary(
	stage: AgentStageSummary | null,
): stage is AgentStageSummary {
	return stage !== null;
}

function normalizeVerifier(value: unknown): SnapshotVerifierResult | null {
	if (!isRecord(value)) {
		return null;
	}

	const confidence =
		typeof value.confidence === "number" ? value.confidence : 0;
	const evidenceCount =
		typeof value.evidence_count === "number" ? value.evidence_count : 0;

	return {
		status:
			value.status === "approved" ||
			value.status === "approved_with_warnings" ||
			value.status === "blocked"
				? value.status
				: "approved_with_warnings",
		confidence: Math.max(0, Math.min(100, Math.round(confidence))),
		blockers: asStringArray(value.blockers),
		warnings: asStringArray(value.warnings),
		evidence_count: Math.max(0, Math.round(evidenceCount)),
		next_best_actions: asStringArray(value.next_best_actions),
	};
}

function normalizeSummary(
	summary: AnalysisSnapshotSummary | Record<string, unknown> | null | undefined,
) {
	if (!isRecord(summary)) {
		return null;
	}

	const stages = Array.isArray(summary.agent_stages)
		? summary.agent_stages.map(normalizeStage).filter(isAgentStageSummary)
		: [];
	const verifier = normalizeVerifier(summary.verifier);

	if (!stages.length || !verifier) {
		return null;
	}

	return { stages, verifier };
}

export default function AnalysisOrchestrationPanel({
	summary,
}: {
	summary: AnalysisSnapshotSummary | Record<string, unknown> | null;
}) {
	const normalized = normalizeSummary(summary);

	if (!normalized) {
		return null;
	}

	const { stages, verifier } = normalized;
	const notes = [...verifier.blockers, ...verifier.warnings].slice(0, 4);
	const nextActions = verifier.next_best_actions.slice(0, 4);

	return (
		<section className="rounded-xl border border-black/10 bg-white/[0.72] p-5 shadow-[0_18px_55px_rgba(15,23,42,0.08)] backdrop-blur-xl">
			<div className="flex flex-wrap items-start justify-between gap-3">
				<div>
					<p className="text-xs font-semibold text-zinc-500">
						Agentic AI pipeline
					</p>
					<h2 className="mt-2 text-lg font-semibold text-zinc-950">
						Verified student intelligence snapshot
					</h2>
				</div>
				<div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-right">
					<p className="text-xs text-emerald-800">Verifier confidence</p>
					<p className="text-2xl font-semibold text-emerald-950">
						{verifier.confidence}%
					</p>
				</div>
			</div>

			<div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
				{stages.map((stage) => (
					<div
						key={`${stage.stage}-${stage.status}`}
						className={`rounded-xl border p-3 ${statusTone[stage.status]}`}
					>
						<p className="text-sm font-semibold">
							{stage.label || stage.stage}
						</p>
						<p className="mt-1 text-xs opacity-80">
							{stage.source.replaceAll("_", " ")}
						</p>
					</div>
				))}
			</div>

			{notes.length ? (
				<div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3">
					<p className="text-sm font-semibold text-amber-900">Verifier notes</p>
					<ul className="mt-2 space-y-1 text-sm text-amber-800">
						{notes.map((item) => (
							<li key={item}>{item}</li>
						))}
					</ul>
				</div>
			) : null}

			{nextActions.length ? (
				<div className="mt-4">
					<p className="text-sm font-semibold text-zinc-950">
						Next best actions
					</p>
					<ul className="mt-2 grid gap-2 text-sm text-zinc-700 md:grid-cols-2">
						{nextActions.map((action) => (
							<li
								key={action}
								className="rounded-lg border border-black/10 bg-white px-3 py-2"
							>
								{action}
							</li>
						))}
					</ul>
				</div>
			) : null}
		</section>
	);
}
