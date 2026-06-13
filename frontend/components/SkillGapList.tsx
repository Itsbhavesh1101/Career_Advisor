"use client";

type SkillGap = { skill: string; priority: string };

type SkillGapListProps = {
	items: SkillGap[];
};

export default function SkillGapList({ items }: SkillGapListProps) {
	return (
		<div className="rounded-xl border border-black/10 bg-white/[0.72] p-6 shadow-[0_18px_55px_rgba(15,23,42,0.08)] backdrop-blur-xl">
			<h3 className="mb-4 text-base font-semibold text-zinc-950">Skill gaps</h3>
			<ul className="flex flex-wrap gap-2 text-sm text-zinc-700">
				{items.map((gap) => (
					<li
						key={`${gap.skill}-${gap.priority}`}
						className="flex items-center gap-2 rounded-full border border-orange-200 bg-orange-50 px-3 py-1 text-orange-900"
					>
						<span>{gap.skill}</span>
						<span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-orange-700">
							{gap.priority.toUpperCase()}
						</span>
					</li>
				))}
			</ul>
		</div>
	);
}
