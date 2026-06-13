"use client";

import { ScoreBar } from "@/components/ui";

type EmployabilityChartProps = {
	scores: {
		academic_strength: number;
		technical_skills: number;
		industry_readiness: number;
		resume_quality: number;
	};
};

export default function EmployabilityChart({
	scores,
}: EmployabilityChartProps) {
	const data = [
		{ label: "Academic", value: scores.academic_strength },
		{ label: "Technical", value: scores.technical_skills },
		{ label: "Industry", value: scores.industry_readiness },
		{ label: "Resume", value: scores.resume_quality },
	];

	return (
		<div className="w-full rounded-xl border border-black/10 bg-white/[0.72] p-6 shadow-[0_18px_55px_rgba(15,23,42,0.08)] backdrop-blur-xl">
			<h3 className="text-base font-semibold text-zinc-950">
				Employability breakdown
			</h3>
			<p className="text-sm text-zinc-600">
				Placement readiness across key areas
			</p>
			<div className="mt-5 grid gap-4 sm:grid-cols-2">
				{data.map((item) => (
					<div
						key={item.label}
						className="rounded-lg border border-black/10 bg-white/60 p-4"
					>
						<ScoreBar value={item.value} label={item.label} />
					</div>
				))}
			</div>
		</div>
	);
}
