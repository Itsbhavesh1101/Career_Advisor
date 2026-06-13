"use client";

type InsightPanelProps = {
	traits: Record<string, number>;
	aiStatus?: string;
	adaptationReason?: string | null;
	nextFocus?: string | null;
};

const formatTrait = (name: string) =>
	name.replace(/_/g, " ").replace(/\b\w/g, (ch) => ch.toUpperCase());

function statusLabel(status?: string): string {
	if (status === "ai_generated") return "AI adapting";
	if (status === "guided_adaptive") return "Guided adaptive";
	if (status === "recovering") return "Recalibrating";
	return "Calibrating";
}

export default function InsightPanel({
	traits,
	aiStatus,
	adaptationReason,
	nextFocus,
}: InsightPanelProps) {
	const topTraits = Object.entries(traits)
		.sort((a, b) => b[1] - a[1])
		.slice(0, 3);

	return (
		<aside className="rounded-xl border border-black/10 bg-white/[0.72] p-5 shadow-[0_18px_55px_rgba(15,23,42,0.08)] backdrop-blur-xl">
			<div className="flex items-center justify-between gap-3">
				<p className="text-xs font-semibold text-zinc-500">Live insights</p>
				<span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-800">
					{statusLabel(aiStatus)}
				</span>
			</div>
			<div className="mt-4 space-y-3">
				{topTraits.map(([trait, value]) => (
					<div key={trait} className="space-y-1.5">
						<div className="flex items-center justify-between text-sm text-zinc-700">
							<span>{formatTrait(trait)}</span>
							<span>{Math.round(value * 100)}%</span>
						</div>
						<div className="h-1.5 overflow-hidden rounded-full bg-zinc-200">
							<div
								className="h-full rounded-full bg-orange-500 transition-all duration-500"
								style={{
									width: `${Math.max(6, Math.min(100, Math.round(value * 100)))}%`,
								}}
							/>
						</div>
					</div>
				))}
			</div>
			<div className="mt-5 rounded-xl border border-black/10 bg-orange-50/70 p-4">
				<p className="text-xs font-semibold text-orange-800">Next focus</p>
				<p className="mt-1 text-sm font-semibold text-zinc-950">
					{nextFocus || "Profile calibration"}
				</p>
				<p className="mt-2 text-xs leading-relaxed text-zinc-600">
					{adaptationReason ||
						"The quiz is balancing confidence across your career traits."}
				</p>
			</div>
		</aside>
	);
}
