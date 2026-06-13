"use client";

import {
	CompactActionList,
	GlassPanel,
	StatusBadge,
	Tag,
} from "@/components/ui";

type RoleGapPanelProps = {
	items: {
		role: string;
		missing_skills: string[];
		learning_plan: string[];
		current_evidence?: string[];
		gap_reason?: string | null;
		next_project?: string | null;
		proof_to_build?: string[];
		priority?: string | null;
	}[];
};

function priorityTone(
	priority?: string | null,
): "danger" | "warning" | "orange" {
	if (!priority) return "orange";
	const value = priority.toLowerCase();
	if (value.includes("urgent") || value.includes("high")) return "danger";
	if (value.includes("medium")) return "warning";
	return "orange";
}

export default function RoleGapPanel({ items }: RoleGapPanelProps) {
	return (
		<GlassPanel className="p-6">
			<div className="mb-5">
				<h3 className="text-lg font-semibold text-zinc-950">
					What to build before applying
				</h3>
				<p className="mt-1 text-sm text-zinc-600">
					Each role maps missing skills to concrete proof, not only course
					names.
				</p>
			</div>

			<div className="space-y-4">
				{items.map((role) => (
					<article
						key={role.role}
						className="rounded-xl border border-black/10 bg-white/70 p-4"
					>
						<div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
							<p className="text-base font-semibold text-zinc-950">
								{role.role}
							</p>
							<div className="flex flex-wrap gap-2">
								{role.priority ? (
									<StatusBadge tone={priorityTone(role.priority)}>
										{role.priority}
									</StatusBadge>
								) : null}
								<Tag>{role.missing_skills.length} gaps</Tag>
							</div>
						</div>

						{role.gap_reason ? (
							<p className="mt-3 text-sm text-zinc-600">{role.gap_reason}</p>
						) : null}

						<div className="mt-4 flex flex-wrap gap-2">
							{role.missing_skills.length ? (
								role.missing_skills.map((skill) => (
									<Tag key={skill} tone="danger">
										{skill}
									</Tag>
								))
							) : (
								<Tag tone="success">No major gaps</Tag>
							)}
						</div>

						<div className="mt-4 grid gap-3 md:grid-cols-3">
							<div>
								<p className="mb-2 text-xs font-semibold text-zinc-500">
									Current evidence
								</p>
								<CompactActionList
									items={role.current_evidence ?? []}
									emptyText="No evidence captured."
								/>
							</div>
							<div>
								<p className="mb-2 text-xs font-semibold text-zinc-500">
									Learning plan
								</p>
								<CompactActionList
									items={role.learning_plan}
									emptyText="No learning steps."
								/>
							</div>
							<div>
								<p className="mb-2 text-xs font-semibold text-zinc-500">
									Proof to build
								</p>
								<CompactActionList
									items={[
										...(role.next_project ? [role.next_project] : []),
										...(role.proof_to_build ?? []),
									]}
									emptyText="No proof target yet."
								/>
							</div>
						</div>
					</article>
				))}
			</div>
		</GlassPanel>
	);
}
