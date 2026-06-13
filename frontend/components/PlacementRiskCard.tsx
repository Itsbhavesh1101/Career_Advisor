"use client";

type PlacementRiskCardProps = {
	level: string;
	reasons: string[];
};

const LEVEL_STYLES: Record<string, { badge: string; text: string }> = {
	High: { badge: "bg-red-50 text-red-800 border-red-200", text: "High" },
	Medium: {
		badge: "bg-amber-50 text-amber-800 border-amber-200",
		text: "Medium",
	},
	Low: {
		badge: "bg-emerald-50 text-emerald-800 border-emerald-200",
		text: "Low",
	},
};

export default function PlacementRiskCard({
	level,
	reasons,
}: PlacementRiskCardProps) {
	const style = LEVEL_STYLES[level] ?? LEVEL_STYLES.Medium;

	return (
		<div className="rounded-xl border border-black/10 bg-white/[0.72] p-6 shadow-[0_18px_55px_rgba(15,23,42,0.08)] backdrop-blur-xl">
			<div className="flex items-center justify-between">
				<h3 className="text-sm font-semibold text-zinc-700">Placement risk</h3>
				<span
					className={`rounded-full border px-3 py-1 text-xs font-semibold ${style.badge}`}
				>
					{style.text.toUpperCase()}
				</span>
			</div>
			<p className="mt-3 text-2xl font-semibold text-zinc-950">
				{style.text} risk
			</p>
			<ul className="mt-3 space-y-1 text-xs text-zinc-600">
				{reasons.map((reason) => (
					<li key={reason}>- {reason}</li>
				))}
			</ul>
		</div>
	);
}
