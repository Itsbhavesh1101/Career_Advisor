"use client";

type RoadmapStage = { stage: string; topics?: string[]; items?: string[] };

type LearningRoadmapProps = {
	stages: RoadmapStage[];
};

export default function LearningRoadmap({ stages }: LearningRoadmapProps) {
	const safeStages = stages.filter((stage) => stage?.stage);

	return (
		<div className="rounded-xl border border-black/10 bg-white p-6 shadow-sm">
			<h3 className="mb-4 text-base font-semibold text-zinc-950">
				Learning roadmap
			</h3>
			{safeStages.length === 0 ? (
				<p className="text-sm text-zinc-500">
					No roadmap stages available yet.
				</p>
			) : null}
			<div className="space-y-5">
				{safeStages.map((stage, index) => {
					const topics = stage.topics ?? stage.items ?? [];
					return (
						<div key={stage.stage} className="flex gap-4">
							<div className="flex flex-col items-center">
								<div className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-950 text-sm font-semibold text-white">
									{index + 1}
								</div>
								{index < safeStages.length - 1 ? (
									<div className="mt-2 h-full w-px bg-black/10" />
								) : null}
							</div>
							<div className="rounded-xl border border-black/10 bg-zinc-50 p-4">
								<p className="text-sm font-semibold text-zinc-950">
									{stage.stage}
								</p>
								<p className="mt-2 text-xs text-zinc-600">
									{topics.length
										? topics.join(", ")
										: "Next learning tasks pending."}
								</p>
							</div>
						</div>
					);
				})}
			</div>
		</div>
	);
}
