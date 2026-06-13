"use client";

import { ScoreBar } from "@/components/ui";

type CareerChartProps = {
	data: { role: string; score: number }[];
};

export default function CareerChart({ data }: CareerChartProps) {
	const rows = data.slice(0, 6);

	return (
		<div className="w-full rounded-xl border border-black/10 bg-white/[0.72] p-6 shadow-[0_18px_55px_rgba(15,23,42,0.08)] backdrop-blur-xl">
			<div>
				<h3 className="text-base font-semibold text-zinc-950">
					Career recommendations
				</h3>
				<p className="text-sm text-zinc-600">
					Top career paths based on your profile
				</p>
			</div>
			<div className="mt-5 space-y-4">
				{rows.length ? (
					rows.map((item) => (
						<div key={item.role} className="space-y-1">
							<div className="flex items-center justify-between gap-3 text-sm">
								<span className="break-words font-semibold text-zinc-800">
									{item.role}
								</span>
								<span className="shrink-0 font-semibold text-orange-700">
									{item.score}%
								</span>
							</div>
							<ScoreBar value={item.score} />
						</div>
					))
				) : (
					<p className="text-sm text-zinc-500">
						No career recommendations are available yet.
					</p>
				)}
			</div>
		</div>
	);
}
