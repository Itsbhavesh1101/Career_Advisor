"use client";

import { CompactActionList, GlassPanel, ScoreBar, Tag } from "@/components/ui";

type CompanyFitChartProps = {
	data: {
		company: string;
		company_type?: string | null;
		target_roles?: string[];
		score: number;
		rationale?: string | null;
		matched_evidence?: string[];
		missing_requirements?: string[];
		preparation_plan?: string[];
		hiring_signal_summary?: string | null;
	}[];
};

export default function CompanyFitChart({ data }: CompanyFitChartProps) {
	return (
		<GlassPanel className="p-6">
			<div className="mb-5">
				<h3 className="text-lg font-semibold text-zinc-950">
					Company fit with evidence and blockers
				</h3>
				<p className="mt-1 text-sm text-zinc-600">
					Readiness is based on captured profile evidence, not guaranteed
					shortlisting.
				</p>
			</div>

			<div className="space-y-4">
				{data.map((item) => {
					const score = Math.max(0, Math.min(item.score, 100));
					return (
						<article
							key={item.company}
							className="rounded-xl border border-black/10 bg-white/70 p-4"
						>
							<div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
								<div className="min-w-0">
									<h4 className="break-words text-base font-semibold text-zinc-950">
										{item.company}
									</h4>
									<p className="mt-1 text-xs text-zinc-500">
										{item.company_type ?? "Recruiter pattern"}
									</p>
									<div className="mt-2 flex flex-wrap gap-1.5">
										{item.target_roles?.slice(0, 4).map((role) => (
											<Tag key={role}>{role}</Tag>
										))}
									</div>
								</div>
								<div className="w-full sm:w-48">
									<ScoreBar
										value={score}
										label="ready"
										tone={score >= 70 ? "success" : "warning"}
									/>
								</div>
							</div>

							{item.rationale ? (
								<p className="mt-3 text-sm text-zinc-600">{item.rationale}</p>
							) : null}
							{item.hiring_signal_summary ? (
								<p className="mt-2 text-sm font-semibold text-orange-800">
									{item.hiring_signal_summary}
								</p>
							) : null}

							<div className="mt-4 grid gap-3 md:grid-cols-3">
								<div>
									<p className="mb-2 text-xs font-semibold text-zinc-500">
										Matched evidence
									</p>
									<CompactActionList
										items={item.matched_evidence ?? []}
										emptyText="No evidence matched yet."
									/>
								</div>
								<div>
									<p className="mb-2 text-xs font-semibold text-zinc-500">
										Blockers
									</p>
									<CompactActionList
										items={item.missing_requirements ?? []}
										emptyText="No blockers flagged."
									/>
								</div>
								<div>
									<p className="mb-2 text-xs font-semibold text-zinc-500">
										Next actions
									</p>
									<CompactActionList
										items={item.preparation_plan ?? []}
										emptyText="No plan yet."
									/>
								</div>
							</div>
						</article>
					);
				})}
			</div>
		</GlassPanel>
	);
}
