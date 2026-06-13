"use client";

import { motion } from "framer-motion";
import { use, useEffect, useState } from "react";
import AnalysisOrchestrationPanel from "@/components/AnalysisOrchestrationPanel";
import BranchIntelligencePanel from "@/components/BranchIntelligencePanel";
import CareerChart from "@/components/CareerChart";
import CompanyFitChart from "@/components/CompanyFitChart";
import EmployabilityChart from "@/components/EmployabilityChart";
import LearningRoadmap from "@/components/LearningRoadmap";
import PlacementRiskCard from "@/components/PlacementRiskCard";
import RoleGapPanel from "@/components/RoleGapPanel";
import SkillGapList from "@/components/SkillGapList";
import {
	buttonClass,
	GlassPanel,
	MetricTile,
	Notice,
	PageHeader,
	PageShell,
	SectionTabs,
} from "@/components/ui";
import { LONG_WAIT_NOTICE, toGentleAiMessage } from "@/lib/aiUx";
import {
	type AnalysisSnapshotSummary,
	type CareerAnalysisRead,
	type CompanyFitRead,
	computeEmployabilityScore,
	type EmployabilityScoreRead,
	formatINR,
	generateAnalysis,
	generateCompanyFit,
	generatePlacementRisk,
	generateRoleGaps,
	getAnalysis,
	getCompanyFit,
	getEmployabilityScore,
	getJobStatus,
	getPlacementRisk,
	getProfile,
	getRoleGaps,
	type PlacementRiskRead,
	type RoleGapRead,
	type StudentProfileRead,
} from "@/lib/api";
import { clearStoredProfileId } from "@/lib/profile";
import { useDelayedFlag } from "@/lib/useDelayedFlag";

type AnalysisPageProps = {
	params: Promise<{ id: string }>;
};

type AnalysisTab = "plan" | "evidence" | "details";

const tabs: Array<{ id: AnalysisTab; label: string }> = [
	{ id: "plan", label: "Action plan" },
	{ id: "evidence", label: "Evidence" },
	{ id: "details", label: "Details" },
];

const formatSalaryRange = (analysis: CareerAnalysisRead) => {
	const { currency, estimate_min, estimate_max } = analysis.salary_insights;
	if (currency === "INR") {
		return `${formatINR(estimate_min)} - ${formatINR(estimate_max)}`;
	}
	const formatter = new Intl.NumberFormat("en-US", {
		style: "currency",
		currency,
		maximumFractionDigits: 0,
	});
	return `${formatter.format(estimate_min)} - ${formatter.format(estimate_max)}`;
};

export default function AnalysisPage({ params }: AnalysisPageProps) {
	const { id } = use(params);
	const profileId = Number(id);
	const [analysis, setAnalysis] = useState<CareerAnalysisRead | null>(null);
	const [profile, setProfile] = useState<StudentProfileRead | null>(null);
	const [companyFit, setCompanyFit] = useState<CompanyFitRead | null>(null);
	const [roleGaps, setRoleGaps] = useState<RoleGapRead | null>(null);
	const [placementRisk, setPlacementRisk] = useState<PlacementRiskRead | null>(
		null,
	);
	const [employability, setEmployability] =
		useState<EmployabilityScoreRead | null>(null);
	const [snapshotSummary, setSnapshotSummary] = useState<
		AnalysisSnapshotSummary | Record<string, unknown> | null
	>(null);
	const [loading, setLoading] = useState(true);
	const [generating, setGenerating] = useState(false);
	const [rerunning, setRerunning] = useState(false);
	const [missing, setMissing] = useState(false);
	const [jobMessage, setJobMessage] = useState<string | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [activeTab, setActiveTab] = useState<AnalysisTab>("plan");
	const showLongWaitHint = useDelayedFlag(
		loading || generating || rerunning,
		8000,
	);

	const isTwelfth = profile?.user_type === "twelfth_student";
	const careerRecommendations = analysis?.career_recommendations ?? [];
	const skillGaps = analysis?.skill_gaps ?? [];
	const learningRoadmap = analysis?.learning_roadmap ?? [];
	const industryTrends = analysis?.industry_trends ?? [];
	const topRole = careerRecommendations[0];
	const salaryRange = analysis?.salary_insights
		? formatSalaryRange(analysis)
		: "Not estimated yet";

	useEffect(() => {
		let mounted = true;

		async function load() {
			setLoading(true);
			setError(null);
			setMissing(false);
			setSnapshotSummary(null);
			try {
				const profileData = await getProfile(profileId);
				if (mounted) setProfile(profileData);

				const data = await getAnalysis(profileId);
				if (mounted) setAnalysis(data);

				if (profileData.user_type !== "twelfth_student") {
					try {
						const score = await getEmployabilityScore(profileId);
						if (mounted) setEmployability(score);
					} catch {
						const score = await computeEmployabilityScore(profileId);
						if (mounted) setEmployability(score);
					}
					try {
						const fit = await getCompanyFit(profileId);
						if (mounted) setCompanyFit(fit);
					} catch {
						const fit = await generateCompanyFit(profileId);
						if (mounted) setCompanyFit(fit);
					}
					try {
						const gaps = await getRoleGaps(profileId);
						if (mounted) setRoleGaps(gaps);
					} catch {
						const gaps = await generateRoleGaps(profileId);
						if (mounted) setRoleGaps(gaps);
					}
					try {
						const risk = await getPlacementRisk(profileId);
						if (mounted) setPlacementRisk(risk);
					} catch {
						const risk = await generatePlacementRisk(profileId);
						if (mounted) setPlacementRisk(risk);
					}
				}
			} catch (err) {
				if (!mounted) return;
				setAnalysis(null);
				const message =
					err instanceof Error ? err.message : "Failed to load analysis.";
				if (message.toLowerCase().includes("not found")) {
					clearStoredProfileId();
					setMissing(true);
				} else {
					setError(toGentleAiMessage(message));
				}
			} finally {
				if (mounted) setLoading(false);
			}
		}

		if (!Number.isNaN(profileId)) {
			void load();
		} else {
			setLoading(false);
		}

		return () => {
			mounted = false;
		};
	}, [profileId]);

	async function waitForAnalysisJob(jobId: string) {
		const timeoutMs = 2 * 60 * 1000;
		const pollIntervalMs = 1500;
		const start = Date.now();

		while (Date.now() - start < timeoutMs) {
			const envelope = await getJobStatus(jobId);
			const job = envelope.job;
			setJobMessage(job.message || `Job ${job.status} (${job.progress}%)`);

			if (job.status === "completed") {
				setSnapshotSummary(job.snapshot_summary ?? null);
				return;
			}
			if (job.status === "failed") {
				throw new Error(toGentleAiMessage(job.error || "Analysis job failed."));
			}

			await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
		}

		throw new Error(
			"AI analysis is taking longer than expected. Please try again in a moment.",
		);
	}

	async function handleGenerate() {
		setGenerating(true);
		setError(null);
		setSnapshotSummary(null);
		try {
			const dispatch = await generateAnalysis(profileId);
			await waitForAnalysisJob(dispatch.job_id);
			setAnalysis(await getAnalysis(profileId));
			setMissing(false);
		} catch (err) {
			const message =
				err instanceof Error ? err.message : "Failed to generate analysis.";
			setError(toGentleAiMessage(message));
		} finally {
			setJobMessage(null);
			setGenerating(false);
		}
	}

	async function handleRerun() {
		setRerunning(true);
		setError(null);
		setSnapshotSummary(null);
		try {
			const dispatch = await generateAnalysis(profileId);
			await waitForAnalysisJob(dispatch.job_id);
			const data = await getAnalysis(profileId);
			setAnalysis(data);
			setMissing(false);
			if (profile?.user_type !== "twelfth_student") {
				setEmployability(await computeEmployabilityScore(profileId));
				setCompanyFit(await generateCompanyFit(profileId));
				setRoleGaps(await generateRoleGaps(profileId));
				setPlacementRisk(await generatePlacementRisk(profileId));
			}
		} catch (err) {
			const message =
				err instanceof Error ? err.message : "Failed to re-run analysis.";
			setError(toGentleAiMessage(message));
		} finally {
			setJobMessage(null);
			setRerunning(false);
		}
	}

	return (
		<PageShell>
			<PageHeader
				title={isTwelfth ? "Branch and program guidance" : "Career analysis"}
				description={
					isTwelfth
						? "Best-fit program guidance, expectation checks, evidence, and first-year actions."
						: "Role recommendations, skill gaps, company fit, resume signals, and placement actions."
				}
				actions={
					!loading && analysis ? (
						<button
							type="button"
							onClick={handleRerun}
							disabled={rerunning}
							className={buttonClass()}
						>
							{rerunning ? "Re-running..." : "Re-run AI analysis"}
						</button>
					) : null
				}
			/>

			{loading ? (
				<GlassPanel>
					<p className="text-sm text-zinc-600">Loading analysis...</p>
				</GlassPanel>
			) : null}

			{!loading && Number.isNaN(profileId) ? (
				<Notice title="Invalid profile ID" tone="danger" />
			) : null}

			{!loading && missing ? (
				<GlassPanel className="space-y-3 p-6">
					<p className="text-sm font-semibold text-zinc-950">
						{isTwelfth
							? "No branch guidance found for this profile."
							: "No AI analysis found for this profile."}
					</p>
					<p className="text-sm text-zinc-600">
						{isTwelfth
							? "Generate branch guidance to see best-fit programs, expectation checks, and first-year actions."
							: "Generate career insights to see recommendations, skill gaps, and learning roadmap."}
					</p>
					<button
						type="button"
						onClick={handleGenerate}
						disabled={generating}
						className={buttonClass()}
					>
						{generating
							? "Generating AI insights..."
							: isTwelfth
								? "Generate branch guidance"
								: "Generate career insights"}
					</button>
				</GlassPanel>
			) : null}

			{error ? (
				<Notice
					title="Analysis could not load"
					description={error}
					tone="danger"
				/>
			) : null}
			{jobMessage ? <Notice title={jobMessage} tone="neutral" /> : null}
			{showLongWaitHint && !error ? (
				<Notice
					title="Still working"
					description={LONG_WAIT_NOTICE}
					tone="warning"
				/>
			) : null}

			{analysis ? (
				<motion.div
					initial={{ opacity: 0, y: 12 }}
					animate={{ opacity: 1, y: 0 }}
					transition={{ duration: 0.5 }}
					className="space-y-6"
				>
					<SectionTabs
						items={tabs}
						active={activeTab}
						onChange={setActiveTab}
					/>

					{activeTab === "plan" ? (
						<div className="space-y-6">
							<div className="grid gap-4 md:grid-cols-3">
								<MetricTile
									label={isTwelfth ? "Best-fit path" : "Top role"}
									value={
										isTwelfth
											? analysis.recommended_branch || topRole?.role || "-"
											: topRole?.role || "-"
									}
									helper={`Fit score ${topRole?.score ?? analysis.program_fit_summary?.confidence ?? "-"}`}
									tone="orange"
								/>
								<MetricTile
									label="Skill gaps"
									value={skillGaps.length}
									helper="Focus for next 90 days"
									tone={skillGaps.length ? "warning" : "success"}
								/>
								<MetricTile
									label="Roadmap"
									value={learningRoadmap.length}
									helper="Structured stages"
									tone="success"
								/>
							</div>

							{isTwelfth ? (
								<BranchIntelligencePanel analysis={analysis} />
							) : (
								<div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
									<div className="space-y-6">
										<CareerChart data={careerRecommendations} />
										{companyFit ? (
											<CompanyFitChart data={companyFit.matches} />
										) : null}
										{employability ? (
											<GlassPanel className="p-6">
												<p className="text-sm font-semibold text-zinc-600">
													Employability score
												</p>
												<div className="mt-3 flex items-end justify-between">
													<p className="text-4xl font-semibold text-zinc-950">
														{employability.overall_score}
													</p>
													<p className="text-sm text-zinc-500">out of 100</p>
												</div>
											</GlassPanel>
										) : null}
										<SkillGapList items={skillGaps} />
										<LearningRoadmap stages={learningRoadmap} />
										{roleGaps ? (
											<RoleGapPanel items={roleGaps.role_gaps} />
										) : null}
									</div>
									<div className="space-y-6">
										{employability ? (
											<EmployabilityChart
												scores={{
													academic_strength: employability.academic_strength,
													technical_skills: employability.technical_skills,
													industry_readiness: employability.industry_readiness,
													resume_quality: employability.resume_quality,
												}}
											/>
										) : null}
										{placementRisk ? (
											<PlacementRiskCard
												level={placementRisk.risk_level}
												reasons={placementRisk.reasons}
											/>
										) : null}
										<GlassPanel className="p-6">
											<h3 className="text-sm font-semibold text-zinc-600">
												Estimated entry-level salary
											</h3>
											<p className="mt-3 text-3xl font-bold text-zinc-950">
												{salaryRange}
											</p>
											<p className="mt-2 text-sm text-zinc-500">
												Entry-level role range
											</p>
										</GlassPanel>
										<GlassPanel className="p-6">
											<h3 className="mb-3 text-sm font-semibold text-zinc-700">
												Industry trends
											</h3>
											<ul className="space-y-2 text-sm text-zinc-600">
												{industryTrends.map((trend) => (
													<li
														key={`${trend.trend}-${trend.impact}`}
														className="flex items-center justify-between gap-3"
													>
														<span>{trend.trend}</span>
														<span className="rounded-full bg-orange-50 px-2 py-0.5 text-xs font-semibold text-orange-800">
															{trend.impact.toUpperCase()}
														</span>
													</li>
												))}
											</ul>
										</GlassPanel>
									</div>
								</div>
							)}
						</div>
					) : null}

					{activeTab === "evidence" ? (
						<div className="space-y-5">
							<AnalysisOrchestrationPanel summary={snapshotSummary} />
							<BranchIntelligencePanel analysis={analysis} />
						</div>
					) : null}

					{activeTab === "details" ? (
						<div className="space-y-5">
							<SkillGapList items={skillGaps} />
							<LearningRoadmap stages={learningRoadmap} />
						</div>
					) : null}
				</motion.div>
			) : null}
		</PageShell>
	);
}
