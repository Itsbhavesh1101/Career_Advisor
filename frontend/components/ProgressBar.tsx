"use client";

type ProgressBarProps = {
	answered: number;
	minQuestions: number;
	maxQuestions: number;
	confidence: number;
};

export default function ProgressBar({
	answered,
	minQuestions,
	maxQuestions,
	confidence,
}: ProgressBarProps) {
	const completion = Math.min(
		100,
		(answered / Math.max(maxQuestions, 1)) * 100,
	);
	const confidencePercent = Math.round(
		Math.max(0, Math.min(1, confidence)) * 100,
	);
	const floorReached = answered >= minQuestions;

	return (
		<section className="rounded-xl border border-black/10 bg-white/[0.72] p-4 shadow-[0_18px_55px_rgba(15,23,42,0.08)] backdrop-blur-xl">
			<div className="flex items-center justify-between text-xs font-semibold text-zinc-500">
				<span>Progress</span>
				<span>
					{answered}/{maxQuestions}
				</span>
			</div>
			<div className="mt-3 h-2 rounded-full bg-zinc-200">
				<div
					className="h-2 rounded-full bg-orange-500 transition-all"
					style={{ width: `${completion}%` }}
				/>
			</div>
			<div className="mt-3 flex items-center justify-between text-sm text-zinc-600">
				<span>Confidence {confidencePercent}%</span>
				<span className={floorReached ? "text-emerald-700" : "text-amber-700"}>
					{floorReached
						? "Min floor reached"
						: `Need ${Math.max(0, minQuestions - answered)} more`}
				</span>
			</div>
		</section>
	);
}
