"use client";

import {
	CompactActionList,
	EvidenceDrawer,
	GlassPanel,
	ScoreBar,
	StatusBadge,
	Tag,
} from "@/components/ui";
import type { CareerAnalysisRead } from "@/lib/api";

type BranchIntelligencePanelProps = {
	analysis: CareerAnalysisRead;
};

type NormalizedRAGEvidence = {
	key: string;
	sourceTitle: string;
	sourceType: string;
	excerpt: string;
	reviewStatus: string | null;
	freshnessStatus: string | null;
};

function normalizeRagEvidence(
	analysis: CareerAnalysisRead,
): NormalizedRAGEvidence[] {
	if (!Array.isArray(analysis.rag_evidence)) return [];

	return analysis.rag_evidence
		.map((item, idx) => {
			if (
				typeof item?.source_title !== "string" ||
				typeof item.source_type !== "string" ||
				typeof item.excerpt !== "string"
			) {
				return null;
			}
			const sourceTitle = item.source_title.trim();
			const sourceType = item.source_type.trim();
			const excerpt = item.excerpt.trim();
			if (!sourceTitle || !sourceType || !excerpt) return null;
			return {
				key: `${item.chunk_id || "rag"}-${idx}`,
				sourceTitle,
				sourceType,
				excerpt,
				reviewStatus: item.source_review_status ?? null,
				freshnessStatus: item.source_freshness_status ?? null,
			};
		})
		.filter((item): item is NormalizedRAGEvidence => Boolean(item));
}

export default function BranchIntelligencePanel({
	analysis,
}: BranchIntelligencePanelProps) {
	const programRecommendations = Array.isArray(analysis.program_recommendations)
		? analysis.program_recommendations.filter(
				(program) => program?.program_id && program.program_name,
			)
		: [];
	const expectationRealityChecks = Array.isArray(
		analysis.expectation_reality_checks,
	)
		? analysis.expectation_reality_checks
		: [];
	const roadmap = Array.isArray(analysis.first_year_roadmap)
		? analysis.first_year_roadmap
		: [];
	const ragEvidence = normalizeRagEvidence(analysis);
	const summary = analysis.program_fit_summary;
	const aimlFallback =
		!summary && !programRecommendations.length && analysis.recommended_branch;

	if (aimlFallback) {
		return (
			<GlassPanel className="p-6">
				<h2 className="text-2xl font-semibold text-zinc-950">
					Branch recommendation
				</h2>
				<p className="mt-2 text-sm text-zinc-600">
					{analysis.recommended_branch}
				</p>
				<div className="mt-5">
					<ScoreBar
						value={Math.max(0, Math.min(100, analysis.aiml_score ?? 0))}
						label="AIML fit"
					/>
				</div>
				<div className="mt-5">
					<CompactActionList
						items={(analysis.branch_reasoning ?? []).map((item) => item.reason)}
						emptyText="No branch reasoning available."
					/>
				</div>
			</GlassPanel>
		);
	}

	if (!summary && programRecommendations.length === 0) {
		return null;
	}

	return (
		<div className="space-y-5">
			<GlassPanel className="p-6">
				<div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
					<div className="max-w-2xl">
						<p className="text-sm font-semibold text-orange-700">
							Program guidance
						</p>
						<h2 className="mt-2 text-2xl font-semibold text-zinc-950">
							{summary?.recommended_program_name ?? "Best-fit programs"}
						</h2>
						<p className="mt-2 text-sm leading-6 text-zinc-600">
							{summary?.summary ??
								"Review ranked program options, expectation checks, and evidence before counseling."}
						</p>
					</div>
					{summary?.confidence ? (
						<div className="w-full rounded-xl border border-black/10 bg-white/70 p-4 lg:w-56">
							<ScoreBar
								value={Math.max(0, Math.min(100, summary.confidence))}
								label="confidence"
							/>
						</div>
					) : null}
				</div>
			</GlassPanel>

			{programRecommendations.length > 0 ? (
				<section className="grid gap-4 md:grid-cols-2">
					{programRecommendations.map((program) => {
						const fitScore = Number.isFinite(program.fit_score)
							? Math.max(0, Math.min(program.fit_score, 100))
							: 0;
						return (
							<GlassPanel key={program.program_id} as="article" className="p-5">
								<div className="flex items-start justify-between gap-3">
									<div>
										<p className="text-xs font-semibold text-zinc-500">
											{program.school}
										</p>
										<h3 className="mt-1 text-lg font-semibold text-zinc-950">
											{program.program_name}
										</h3>
									</div>
									<StatusBadge
										tone={program.fit_level === "High" ? "success" : "warning"}
									>
										{program.fit_level}
									</StatusBadge>
								</div>
								<div className="mt-4">
									<ScoreBar value={fitScore} label="fit score" />
								</div>
								<div className="mt-4">
									<CompactActionList
										items={program.reasons ?? []}
										emptyText="No reasons provided."
										limit={3}
									/>
								</div>
								<div className="mt-4 flex flex-wrap gap-2">
									{(program.priority_skills ?? []).slice(0, 5).map((skill) => (
										<Tag key={skill}>{skill}</Tag>
									))}
								</div>
							</GlassPanel>
						);
					})}
				</section>
			) : null}

			{expectationRealityChecks.length ? (
				<GlassPanel className="p-5">
					<h3 className="text-lg font-semibold text-zinc-950">
						Expectation reality check
					</h3>
					<div className="mt-4 grid gap-3 md:grid-cols-3">
						{expectationRealityChecks.slice(0, 3).map((item) => (
							<div
								key={item.expectation}
								className="rounded-lg border border-black/10 bg-white/70 p-4"
							>
								<p className="text-sm font-semibold text-zinc-950">
									{item.expectation}
								</p>
								<p className="mt-2 text-sm text-zinc-600">{item.reality}</p>
							</div>
						))}
					</div>
				</GlassPanel>
			) : null}

			{roadmap.length ? (
				<GlassPanel className="p-5">
					<h3 className="text-lg font-semibold text-zinc-950">
						First-year roadmap
					</h3>
					<div className="mt-4 grid gap-3 md:grid-cols-3">
						{roadmap.map((item) => (
							<div
								key={item.term}
								className="rounded-lg border border-black/10 bg-white/70 p-4"
							>
								<p className="font-semibold text-zinc-950">{item.term}</p>
								<div className="mt-3">
									<CompactActionList
										items={[
											...(item.focus ?? []),
											...(item.evidence_to_build ?? []),
										]}
										emptyText="No actions listed."
									/>
								</div>
							</div>
						))}
					</div>
				</GlassPanel>
			) : null}

			{ragEvidence.length ? (
				<EvidenceDrawer title="Evidence used">
					<div className="space-y-3">
						{ragEvidence.slice(0, 5).map((item) => (
							<div
								key={item.key}
								className="rounded-lg border border-black/10 bg-white/70 p-3"
							>
								<div className="flex flex-wrap gap-2">
									<Tag tone="success">{item.sourceTitle}</Tag>
									<Tag>{item.sourceType}</Tag>
									{item.reviewStatus ? (
										<Tag
											tone={
												item.freshnessStatus === "expired"
													? "warning"
													: "success"
											}
										>
											{item.freshnessStatus === "expired"
												? "expired"
												: item.reviewStatus.replace("_", " ")}
										</Tag>
									) : null}
								</div>
								<p className="mt-2 text-sm text-zinc-600">{item.excerpt}</p>
							</div>
						))}
					</div>
				</EvidenceDrawer>
			) : null}
		</div>
	);
}
