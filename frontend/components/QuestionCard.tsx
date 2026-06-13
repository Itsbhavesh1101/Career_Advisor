"use client";

import type { PsychometricQuestionRead } from "@/lib/api";

type QuestionCardProps = {
	question: PsychometricQuestionRead;
	disabled?: boolean;
	selectedOptionId?: string | null;
	isAdvancing?: boolean;
	onSelect: (optionId: string) => void;
};

function optionClass(isSelected: boolean, disabled: boolean): string {
	const base =
		"group relative overflow-hidden rounded-xl border px-4 py-3 text-left text-sm transition duration-200";
	if (isSelected) {
		return `${base} border-orange-300 bg-orange-50 text-zinc-950 shadow-sm`;
	}
	return `${base} border-black/10 bg-white text-zinc-800 hover:border-orange-300 hover:bg-orange-50 ${
		disabled ? "cursor-not-allowed opacity-60" : ""
	}`;
}

export default function QuestionCard({
	question,
	disabled = false,
	selectedOptionId = null,
	isAdvancing = false,
	onSelect,
}: QuestionCardProps) {
	return (
		<section
			key={question.id}
			className="relative animate-[quizIn_220ms_ease-out] overflow-hidden rounded-xl border border-black/10 bg-white p-6 shadow-[0_8px_26px_rgba(15,23,42,0.05)]"
		>
			<div className="flex items-center justify-between gap-3">
				<p className="text-xs font-semibold text-zinc-500">
					Question {question.position}
				</p>
				<span className="rounded-full border border-orange-200 bg-orange-50 px-2.5 py-1 text-xs font-semibold text-orange-800">
					{question.source === "llm" ? "AI generated" : "Guided adaptive"}
				</span>
			</div>
			<h2 className="mt-3 text-xl font-semibold leading-snug text-zinc-950">
				{question.question_text}
			</h2>
			<div className="mt-5 grid gap-3">
				{question.options.map((option) => (
					<button
						key={`${question.id}-${option.option_id}`}
						type="button"
						disabled={disabled}
						onClick={() => onSelect(option.option_id)}
						className={optionClass(
							option.option_id === selectedOptionId,
							disabled,
						)}
					>
						<span className="relative z-10 block leading-relaxed">
							{option.text}
						</span>
						{option.option_id === selectedOptionId ? (
							<span className="absolute inset-y-0 left-0 w-1 bg-orange-500" />
						) : null}
					</button>
				))}
			</div>
			{isAdvancing ? (
				<div className="absolute inset-0 flex items-center justify-center bg-white/85">
					<div className="rounded-xl border border-black/10 bg-white px-5 py-4 text-center shadow-lg">
						<div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
						<p className="mt-3 text-sm font-medium text-zinc-950">
							Mapping your response
						</p>
						<p className="mt-1 text-xs text-zinc-500">
							Choosing the next best question...
						</p>
					</div>
				</div>
			) : null}
		</section>
	);
}
