"use client";

import Link from "next/link";
import { buttonClass, GlassPanel, StatusBadge, Tag } from "@/components/ui";
import type { StudentProfileRead } from "@/lib/api";
import { getProfileStudentType } from "@/lib/profile";

type ProfileSummaryCardProps = {
	profile: StudentProfileRead;
	onReset?: () => void;
	showSwitch?: boolean;
};

function ValueBlock({ label, value }: { label: string; value?: unknown }) {
	const display = Array.isArray(value)
		? value.filter(Boolean).join(", ")
		: String(value ?? "");
	return (
		<div className="rounded-lg border border-black/10 bg-white/60 p-4">
			<p className="text-sm font-medium text-zinc-500">{label}</p>
			<p className="mt-1 break-words text-base font-semibold text-zinc-950">
				{display || "-"}
			</p>
		</div>
	);
}

export default function ProfileSummaryCard({
	profile,
	onReset,
	showSwitch = false,
}: ProfileSummaryCardProps) {
	const isTwelfth = getProfileStudentType(profile) === "twelfth_student";
	const identityLabel = isTwelfth
		? "12th branch guidance"
		: "College placement readiness";

	return (
		<GlassPanel className="space-y-6">
			<div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
				<div>
					<div className="flex flex-wrap items-center gap-2">
						<h2 className="text-2xl font-semibold tracking-tight text-zinc-950">
							{profile.name}
						</h2>
						<StatusBadge tone={isTwelfth ? "orange" : "dark"}>
							{identityLabel}
						</StatusBadge>
					</div>
					<p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
						This profile powers the quiz, analysis, readiness dashboard, and
						next action loop.
					</p>
				</div>
				{showSwitch ? (
					<Link
						href="/profile"
						className={buttonClass({ variant: "secondary" })}
					>
						Switch profile
					</Link>
				) : null}
			</div>

			<div className="grid gap-3 md:grid-cols-2">
				<ValueBlock
					label="12th percentage"
					value={`${profile.twelfth_percentage ?? "-"}%`}
				/>
				{!isTwelfth ? (
					<>
						<ValueBlock label="CGPA" value={profile.cgpa} />
						<ValueBlock label="Degree" value={profile.degree} />
						<ValueBlock label="Specialization" value={profile.specialization} />
					</>
				) : null}
				<ValueBlock label="Target industry" value={profile.target_industry} />
				{!isTwelfth ? (
					<ValueBlock
						label="Projects / internships / certifications"
						value={`${profile.projects ?? 0} / ${profile.internships ?? 0} / ${profile.certifications ?? 0}`}
					/>
				) : null}
			</div>

			<div className="grid gap-4 md:grid-cols-2">
				<div>
					<p className="text-sm font-semibold text-zinc-700">Interests</p>
					<div className="mt-2 flex flex-wrap gap-2">
						{profile.interests?.length ? (
							profile.interests.map((interest) => (
								<Tag key={interest}>{interest}</Tag>
							))
						) : (
							<Tag tone="warning">Not added</Tag>
						)}
					</div>
				</div>
				{!isTwelfth ? (
					<div>
						<p className="text-sm font-semibold text-zinc-700">
							Current skills
						</p>
						<div className="mt-2 flex flex-wrap gap-2">
							{profile.current_skills?.length ? (
								profile.current_skills.map((skill) => (
									<Tag key={skill} tone="orange">
										{skill}
									</Tag>
								))
							) : (
								<Tag tone="warning">Not added</Tag>
							)}
						</div>
					</div>
				) : null}
			</div>

			<div className="flex flex-col gap-3 border-t border-black/10 pt-5 sm:flex-row sm:items-center sm:justify-between">
				<p className="text-xs text-zinc-500">
					Created {new Date(profile.created_at).toLocaleDateString()}
				</p>
				<div className="flex flex-wrap gap-2">
					<Link
						href={`/profiles/${profile.id}/edit`}
						className={buttonClass({ variant: "primary" })}
					>
						Edit profile
					</Link>
					<Link
						href={`/onboarding/quiz/${profile.id}`}
						className={buttonClass({ variant: "secondary" })}
					>
						{isTwelfth ? "Retake fit quiz" : "Retake readiness quiz"}
					</Link>
					<Link
						href={`/analysis/${profile.id}`}
						className={buttonClass({ variant: "secondary" })}
					>
						{isTwelfth ? "Rerun guidance" : "Rerun analysis"}
					</Link>
					<Link
						href="/dashboard"
						className={buttonClass({ variant: "secondary" })}
					>
						{isTwelfth ? "Open guidance hub" : "Open readiness hub"}
					</Link>
					{onReset ? (
						<button
							type="button"
							onClick={onReset}
							className={buttonClass({
								variant: "ghost",
								className: "text-red-700 hover:border-red-200 hover:bg-red-50",
							})}
						>
							Reset profile
						</button>
					) : null}
				</div>
			</div>
		</GlassPanel>
	);
}
