"use client";

import Link from "next/link";
import { useEffect, useId, useState } from "react";
import {
	buttonClass,
	CompactActionList,
	EmptyState,
	Field,
	fieldControlClass,
	GlassPanel,
	Notice,
	PageHeader,
	PageShell,
	ScoreBar,
	Tag,
} from "@/components/ui";
import { LONG_WAIT_NOTICE, toGentleAiMessage } from "@/lib/aiUx";
import {
	getResumeAnalysis,
	type ResumeAnalysisRead,
	submitResumeUrl,
} from "@/lib/api";
import { getStoredProfileId } from "@/lib/profile";
import { useDelayedFlag } from "@/lib/useDelayedFlag";

export default function ResumePage() {
	const resumeUrlId = useId();
	const [profileId, setProfileId] = useState<number | null>(null);
	const [analysis, setAnalysis] = useState<ResumeAnalysisRead | null>(null);
	const [resumeUrl, setResumeUrl] = useState("");
	const [loading, setLoading] = useState(true);
	const [uploading, setUploading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const showLongWaitHint = useDelayedFlag(uploading || loading, 7000);

	useEffect(() => {
		const stored = getStoredProfileId();
		const id = stored ? Number(stored) : null;
		setProfileId(id && Number.isFinite(id) ? id : null);
	}, []);

	useEffect(() => {
		async function fetchLatest() {
			if (!profileId) {
				setLoading(false);
				return;
			}
			try {
				setAnalysis(await getResumeAnalysis(profileId));
			} catch {
				setAnalysis(null);
			} finally {
				setLoading(false);
			}
		}
		void fetchLatest();
	}, [profileId]);

	async function handleSubmitResumeUrl(
		event: React.FormEvent<HTMLFormElement>,
	) {
		event.preventDefault();
		if (!profileId || !resumeUrl.trim()) return;
		setError(null);
		setUploading(true);
		try {
			setAnalysis(await submitResumeUrl(profileId, resumeUrl.trim()));
		} catch (err) {
			const message =
				err instanceof Error ? err.message : "Failed to analyze resume.";
			setError(toGentleAiMessage(message));
		} finally {
			setUploading(false);
		}
	}

	return (
		<PageShell>
			<PageHeader
				title="Resume readiness"
				description="Extract skills, projects, and missing proof so the placement loop has stronger evidence."
				actions={
					<Link
						href="/dashboard"
						className={buttonClass({ variant: "secondary" })}
					>
						Back to dashboard
					</Link>
				}
			/>

			{!profileId ? (
				<EmptyState
					title="Create a profile first"
					description="Resume analysis needs a saved profile before it can update readiness."
					action={
						<Link href="/create-profile" className={buttonClass()}>
							Create profile
						</Link>
					}
				/>
			) : (
				<GlassPanel className="p-6">
					<form
						onSubmit={handleSubmitResumeUrl}
						className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end"
					>
						<Field label="Resume URL (PDF or DOCX)" htmlFor={resumeUrlId}>
							<input
								id={resumeUrlId}
								type="url"
								value={resumeUrl}
								onChange={(event) => setResumeUrl(event.target.value)}
								placeholder="https://example.com/resume.pdf"
								className={fieldControlClass}
								disabled={uploading}
								required
							/>
						</Field>
						<button
							type="submit"
							disabled={uploading || !resumeUrl.trim()}
							className={buttonClass()}
						>
							{uploading ? "Analyzing..." : "Analyze resume"}
						</button>
					</form>
					{loading ? (
						<p className="mt-3 text-sm text-zinc-500">
							Loading resume analysis...
						</p>
					) : null}
					{showLongWaitHint && !error ? (
						<p className="mt-3 text-sm text-zinc-500">{LONG_WAIT_NOTICE}</p>
					) : null}
				</GlassPanel>
			)}

			{error ? (
				<Notice
					title="Resume analysis failed"
					description={error}
					tone="danger"
				/>
			) : null}

			{analysis ? (
				<div className="grid gap-5 lg:grid-cols-2">
					<GlassPanel className="p-6">
						<h2 className="text-lg font-semibold text-zinc-950">
							Resume score
						</h2>
						<p className="mt-3 text-4xl font-semibold text-zinc-950">
							{analysis.resume_score}/100
						</p>
						<div className="mt-4">
							<ScoreBar value={analysis.resume_score} />
						</div>
						<p className="mt-3 text-sm text-zinc-600">
							Based on skills, projects, experience, and education signals.
						</p>
					</GlassPanel>

					<GlassPanel className="p-6">
						<h2 className="text-lg font-semibold text-zinc-950">
							Missing keywords
						</h2>
						<div className="mt-4 flex flex-wrap gap-2">
							{analysis.missing_keywords.length ? (
								analysis.missing_keywords.map((item) => (
									<Tag key={item} tone="warning">
										{item}
									</Tag>
								))
							) : (
								<Tag tone="success">No missing keywords</Tag>
							)}
						</div>
					</GlassPanel>

					<GlassPanel className="p-6">
						<h2 className="text-lg font-semibold text-zinc-950">
							Extracted skills
						</h2>
						<div className="mt-4 flex flex-wrap gap-2">
							{analysis.extracted_skills.length ? (
								analysis.extracted_skills.map((item) => (
									<Tag key={item}>{item}</Tag>
								))
							) : (
								<Tag>No skills detected</Tag>
							)}
						</div>
					</GlassPanel>

					<GlassPanel className="p-6">
						<h2 className="text-lg font-semibold text-zinc-950">
							Weak sections
						</h2>
						<div className="mt-4 flex flex-wrap gap-2">
							{analysis.weak_sections.length ? (
								analysis.weak_sections.map((item) => (
									<Tag key={item} tone="warning">
										{item}
									</Tag>
								))
							) : (
								<Tag tone="success">No weak sections</Tag>
							)}
						</div>
					</GlassPanel>

					<ResumeList title="Projects" items={analysis.projects} />
					<ResumeList title="Experience" items={analysis.experience} />
					<ResumeList title="Education" items={analysis.education} />
					<ResumeList title="Suggestions" items={analysis.suggestions} />
				</div>
			) : null}
		</PageShell>
	);
}

function ResumeList({ title, items }: { title: string; items: string[] }) {
	return (
		<GlassPanel className="p-6">
			<h2 className="text-lg font-semibold text-zinc-950">{title}</h2>
			<div className="mt-4">
				<CompactActionList
					items={items}
					emptyText={`No ${title.toLowerCase()} detected.`}
				/>
			</div>
		</GlassPanel>
	);
}
