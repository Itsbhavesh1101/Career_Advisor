"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import BranchIntelligencePanel from "@/components/BranchIntelligencePanel";
import {
	buttonClass,
	CompactActionList,
	EmptyState,
	GlassPanel,
	PageHeader,
	StatusBadge,
} from "@/components/ui";
import {
	type CareerAnalysisRead,
	getAnalysis,
	getProfileDashboardSummary,
	listProfiles,
	type StudentDashboardSummaryRead,
	type StudentProfileRead,
} from "@/lib/api";
import {
	getCreateProfileType,
	getProfileStudentType,
	getStoredUserType,
	resolveStoredProfile,
} from "@/lib/profile";

export default function DashboardPage() {
	const router = useRouter();
	const [profile, setProfile] = useState<StudentProfileRead | null>(null);
	const [analysis, setAnalysis] = useState<CareerAnalysisRead | null>(null);
	const [summary, setSummary] = useState<StudentDashboardSummaryRead | null>(
		null,
	);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [isTwelfth, setIsTwelfth] = useState(false);

	useEffect(() => {
		let mounted = true;

		async function load() {
			setLoading(true);
			setError(null);
			try {
				const profiles = await listProfiles();
				if (!mounted) return;

				if (profiles.length === 0) {
					const routeType = getCreateProfileType(getStoredUserType());
					router.push(`/create-profile?type=${routeType}`);
					return;
				}

				const latestProfile = resolveStoredProfile(profiles);
				if (!latestProfile) {
					const routeType = getCreateProfileType(getStoredUserType());
					router.push(`/create-profile?type=${routeType}`);
					return;
				}

				setProfile(latestProfile);
				try {
					setSummary(await getProfileDashboardSummary(latestProfile.id));
				} catch {
					setSummary(null);
				}

				const userIsTwelfth =
					getProfileStudentType(latestProfile) === "twelfth_student";
				setIsTwelfth(userIsTwelfth);

				try {
					setAnalysis(await getAnalysis(latestProfile.id));
				} catch {
					setAnalysis(null);
				}
			} catch (err) {
				if (mounted) {
					setError(
						err instanceof Error ? err.message : "Failed to load dashboard.",
					);
				}
			} finally {
				if (mounted) setLoading(false);
			}
		}

		void load();

		return () => {
			mounted = false;
		};
	}, [router]);

	const topRole = analysis?.career_recommendations?.[0];
	const nextActions = useMemo(
		() =>
			summary?.next_actions?.length
				? summary.next_actions.slice(0, 3)
				: [
						isTwelfth
							? "Complete quiz and generate branch guidance."
							: "Generate career analysis and review skill gaps.",
					],
		[summary, isTwelfth],
	);

	if (loading) {
		return (
			<main className="mx-auto max-w-6xl space-y-5 px-6 py-10">
				<div className="h-28 animate-pulse rounded-xl bg-white/70" />
				<div className="grid gap-4 md:grid-cols-3">
					{[1, 2, 3].map((i) => (
						<div
							key={i}
							className="h-36 animate-pulse rounded-xl bg-white/60"
						/>
					))}
				</div>
			</main>
		);
	}

	if (error) {
		return (
			<main className="mx-auto max-w-6xl px-6 py-10">
				<EmptyState
					title="Dashboard could not load"
					description={error}
					action={
						<Link href="/create-profile" className={buttonClass()}>
							Create profile
						</Link>
					}
				/>
			</main>
		);
	}

	if (!profile) {
		return (
			<main className="mx-auto max-w-6xl px-6 py-10">
				<EmptyState
					title="No profile found"
					description="Create a profile to start branch guidance or placement readiness."
					action={
						<Link href="/create-profile" className={buttonClass()}>
							Create profile
						</Link>
					}
				/>
			</main>
		);
	}

	return (
		<main className="mx-auto max-w-6xl space-y-6 px-6 py-10">
			<PageHeader
				title={
					isTwelfth
						? "Branch guidance workspace"
						: "Placement readiness workspace"
				}
				description={
					isTwelfth
						? "Your profile, quiz, program fit, and branch decision plan in one place."
						: "Your profile, analysis, resume, training, and internship actions in one loop."
				}
				actions={
					<>
						<Link
							href={`/profile/${profile.id}`}
							className={buttonClass({ variant: "secondary" })}
						>
							View profile
						</Link>
						<Link
							href={`/analysis/${profile.id}`}
							className={buttonClass({ variant: "primary" })}
						>
							{analysis ? "Open analysis" : "Generate analysis"}
						</Link>
					</>
				}
			/>

			<section className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
				<GlassPanel tone="orange" className="p-6">
					<div className="flex flex-wrap items-start justify-between gap-4">
						<div>
							<p className="text-sm font-semibold text-orange-800">
								{profile.name}
							</p>
							<h2 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-950">
								Today&apos;s plan
							</h2>
							<p className="mt-2 max-w-xl text-sm leading-6 text-zinc-700">
								{summary?.readiness_summary ||
									(isTwelfth
										? "Complete branch guidance to produce a counselor-ready decision plan."
										: "Complete readiness signals to turn placement goals into concrete actions.")}
							</p>
						</div>
						<StatusBadge tone="orange">
							{isTwelfth ? "12th student" : "college student"}
						</StatusBadge>
					</div>
					<div className="mt-5 rounded-xl border border-orange-200 bg-white/60 p-4">
						<CompactActionList items={nextActions} limit={3} />
					</div>
				</GlassPanel>

				<GlassPanel className="p-6">
					<h2 className="text-xl font-semibold text-zinc-950">
						Where to go next
					</h2>
					<p className="mt-2 text-sm leading-6 text-zinc-600">
						{isTwelfth
							? "Use your profile and fit quiz to refresh program guidance whenever your interests or marks change."
							: "Use your profile, analysis, resume, training, and internship pages as one placement preparation loop."}
					</p>
					<div className="mt-5 grid gap-2">
						<Link
							href={`/profile/${profile.id}`}
							className={buttonClass({ variant: "secondary" })}
						>
							Review profile
						</Link>
						<Link
							href={`/onboarding/quiz/${profile.id}`}
							className={buttonClass({ variant: "secondary" })}
						>
							{isTwelfth ? "Retake fit quiz" : "Retake readiness quiz"}
						</Link>
						<Link
							href={`/analysis/${profile.id}`}
							className={buttonClass({
								variant: analysis ? "secondary" : "primary",
							})}
						>
							{analysis
								? isTwelfth
									? "Open program guidance"
									: "Open career analysis"
								: isTwelfth
									? "Generate program guidance"
									: "Generate career analysis"}
						</Link>
					</div>
				</GlassPanel>
			</section>

			{isTwelfth ? (
				analysis ? (
					<BranchIntelligencePanel analysis={analysis} />
				) : (
					<EmptyState
						title="Branch guidance is not generated yet"
						description="Run the analysis after quiz completion to see best-fit programs and expectation checks."
						action={
							<Link
								href={`/analysis/${profile.id}`}
								className={buttonClass({ variant: "primary" })}
							>
								Generate branch guidance
							</Link>
						}
					/>
				)
			) : (
				<section className="grid gap-4 md:grid-cols-3">
					<GlassPanel>
						<h3 className="text-lg font-semibold text-zinc-950">
							Career outcome
						</h3>
						<p className="mt-2 text-sm text-zinc-600">
							{topRole
								? `${topRole.role} with ${topRole.score} fit score.`
								: "Generate analysis to identify the strongest role path."}
						</p>
					</GlassPanel>
					<GlassPanel>
						<h3 className="text-lg font-semibold text-zinc-950">Resume loop</h3>
						<p className="mt-2 text-sm text-zinc-600">
							Turn resume gaps into evidence for placement readiness.
						</p>
						<Link
							href="/resume"
							className={buttonClass({
								variant: "secondary",
								className: "mt-4",
							})}
						>
							Open resume
						</Link>
					</GlassPanel>
					<GlassPanel>
						<h3 className="text-lg font-semibold text-zinc-950">
							Training loop
						</h3>
						<p className="mt-2 text-sm text-zinc-600">
							Use training programs and industry demand to choose next
							preparation work.
						</p>
						<div className="mt-4 flex flex-wrap gap-2">
							<Link
								href="/training"
								className={buttonClass({ variant: "secondary" })}
							>
								Training
							</Link>
							<Link
								href="/internship"
								className={buttonClass({ variant: "ghost" })}
							>
								Internship
							</Link>
						</div>
					</GlassPanel>
				</section>
			)}
		</main>
	);
}
