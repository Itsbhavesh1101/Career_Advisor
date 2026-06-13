"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
	buttonClass,
	EmptyState,
	GlassPanel,
	MetricTile,
	Notice,
	PageHeader,
	PageShell,
	ScoreBar,
	Tag,
} from "@/components/ui";
import { LONG_WAIT_NOTICE, toGentleAiMessage } from "@/lib/aiUx";
import {
	getIndustryDemand,
	getMe,
	getTrainingRecommendations,
	type IndustryDemandRead,
	type TrainingRecommendationsRead,
} from "@/lib/api";
import { useDelayedFlag } from "@/lib/useDelayedFlag";

export default function TrainingPage() {
	const [data, setData] = useState<TrainingRecommendationsRead | null>(null);
	const [demand, setDemand] = useState<IndustryDemandRead | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [isAdmin, setIsAdmin] = useState(false);
	const showLongWaitHint = useDelayedFlag(loading, 7000);

	useEffect(() => {
		let mounted = true;
		async function load() {
			setLoading(true);
			setError(null);
			try {
				const [result, demandData, me] = await Promise.all([
					getTrainingRecommendations(),
					getIndustryDemand(),
					getMe(),
				]);
				if (mounted) {
					setData(result);
					setDemand(demandData);
					setIsAdmin(me.role === "admin");
				}
			} catch (err) {
				if (mounted) {
					const message =
						err instanceof Error
							? err.message
							: "Failed to load training data.";
					setError(toGentleAiMessage(message));
				}
			} finally {
				if (mounted) setLoading(false);
			}
		}
		void load();
		return () => {
			mounted = false;
		};
	}, []);

	return (
		<PageShell>
			<PageHeader
				title="Training action loop"
				description="Connect weak skills, industry demand, and readiness gaps to concrete training work."
				actions={
					<Link
						href="/dashboard"
						className={buttonClass({ variant: "secondary" })}
					>
						Back to dashboard
					</Link>
				}
			/>

			{loading ? (
				<GlassPanel>
					<p className="text-sm text-zinc-600">Loading recommendations...</p>
				</GlassPanel>
			) : null}
			{loading && showLongWaitHint ? (
				<Notice
					title="Still loading"
					description={LONG_WAIT_NOTICE}
					tone="warning"
				/>
			) : null}
			{error ? (
				<Notice
					title="Training could not load"
					description={error}
					tone="danger"
				/>
			) : null}

			{data ? (
				<>
					<div
						className={`grid gap-4 ${isAdmin ? "md:grid-cols-2" : "md:grid-cols-1"}`}
					>
						{isAdmin ? (
							<MetricTile
								label="Students in cohort"
								value={data.total_students}
								helper="Training population"
								tone="orange"
							/>
						) : null}
						{demand ? (
							<MetricTile
								label={`Industry demand ${demand.year}`}
								value={demand.trends.length}
								helper="Trending skills"
								tone="success"
							/>
						) : null}
					</div>

					<div className={`grid gap-6 ${isAdmin ? "lg:grid-cols-2" : ""}`}>
						{isAdmin ? (
							<GlassPanel className="p-6">
								<h2 className="text-lg font-semibold text-zinc-950">
									Top weak skills
								</h2>
								<p className="mt-2 text-sm leading-6 text-zinc-600">
									Cohort skill gaps are admin-only because they are operational
									signals, not student-facing feedback.
								</p>
								<div className="mt-4 space-y-3">
									{data.weak_skills.length ? (
										data.weak_skills.map((item) => (
											<div
												key={item.skill}
												className="rounded-xl border border-black/10 bg-white/70 px-4 py-3"
											>
												<div className="flex items-center justify-between gap-3">
													<span className="text-sm font-semibold text-zinc-950">
														{item.skill}
													</span>
													<span className="text-xs text-zinc-500">
														{item.count} students
													</span>
												</div>
												<ScoreBar value={Math.min(item.count * 10, 100)} />
											</div>
										))
									) : (
										<p className="text-sm text-zinc-500">No gap data yet.</p>
									)}
								</div>
							</GlassPanel>
						) : null}

						<GlassPanel className="p-6">
							<h2 className="text-lg font-semibold text-zinc-950">
								Recommended training programs
							</h2>
							<p className="mt-2 text-sm leading-6 text-zinc-600">
								Pick the next training action that builds evidence for your
								placement target.
							</p>
							<div className="mt-4 space-y-4">
								{data.programs.length ? (
									data.programs.map((program) => (
										<div
											key={program.title}
											className="rounded-xl border border-black/10 bg-white/70 p-4"
										>
											<h3 className="text-sm font-semibold text-zinc-950">
												{program.title}
											</h3>
											<p className="mt-2 text-xs leading-5 text-zinc-600">
												{program.description}
											</p>
											<div className="mt-3 flex flex-wrap gap-2">
												{program.focus_skills.map((skill) => (
													<Tag key={skill}>{skill}</Tag>
												))}
											</div>
										</div>
									))
								) : (
									<p className="text-sm text-zinc-500">
										No program suggestions yet.
									</p>
								)}
							</div>
						</GlassPanel>

						<GlassPanel className="p-6 lg:col-span-2">
							<h2 className="text-lg font-semibold text-zinc-950">
								Industry demand trends
							</h2>
							<div className="mt-4 grid gap-3 md:grid-cols-2">
								{demand?.trends.length ? (
									demand.trends.map((item) => (
										<div
											key={item.trend}
											className="flex items-center justify-between rounded-xl border border-black/10 bg-white/70 px-4 py-3"
										>
											<span className="text-sm font-semibold text-zinc-950">
												{item.trend}
											</span>
											<Tag tone="orange">{item.impact.toUpperCase()}</Tag>
										</div>
									))
								) : (
									<EmptyState title="No demand data yet" />
								)}
							</div>
						</GlassPanel>
					</div>
				</>
			) : null}
		</PageShell>
	);
}
