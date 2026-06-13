"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
	buttonClass,
	CompactActionList,
	EmptyState,
	GlassPanel,
	MetricTile,
	Notice,
	PageHeader,
	PageShell,
	ScoreBar,
	StatusBadge,
} from "@/components/ui";
import { LONG_WAIT_NOTICE, toGentleAiMessage } from "@/lib/aiUx";
import {
	applyToPlacementOpportunity,
	generateInternshipReadiness,
	getInternshipReadiness,
	type InternshipReadinessRead,
	listManagedInternshipOpportunities,
	listStudentPlacementActivity,
	listStudentPlacementApplications,
	listStudentPlacementOpportunities,
	listStudentPlacementUpcomingActions,
	type ManagedInternshipOpportunityRead,
	type PlacementActivityEventRead,
	type PlacementApplicationRead,
	type PlacementOpportunityRead,
	type PlacementUpcomingActionRead,
	updateStudentPlacementApplication,
} from "@/lib/api";
import {
	buildApplicationNextStep,
	buildMatchReasons,
	buildOpportunityMeta,
	buildStudentPlacementActionLabel,
	canStudentEditApplicationNote,
	canStudentWithdrawApplication,
} from "@/lib/placementOpportunityUi";
import { getStoredProfileId } from "@/lib/profile";
import { useDelayedFlag } from "@/lib/useDelayedFlag";

const LEVEL_TONES: Record<
	string,
	"success" | "warning" | "danger" | "neutral"
> = {
	High: "success",
	Medium: "warning",
	Low: "danger",
};

export default function InternshipPage() {
	const [profileId, setProfileId] = useState<number | null>(null);
	const [data, setData] = useState<InternshipReadinessRead | null>(null);
	const [opportunities, setOpportunities] = useState<
		PlacementOpportunityRead[]
	>([]);
	const [managedInternships, setManagedInternships] = useState<
		ManagedInternshipOpportunityRead[]
	>([]);
	const [applications, setApplications] = useState<PlacementApplicationRead[]>(
		[],
	);
	const [placementActivity, setPlacementActivity] = useState<
		PlacementActivityEventRead[]
	>([]);
	const [upcomingActions, setUpcomingActions] = useState<
		PlacementUpcomingActionRead[]
	>([]);
	const [loading, setLoading] = useState(true);
	const [opportunityLoading, setOpportunityLoading] = useState(false);
	const [generating, setGenerating] = useState(false);
	const [applyingId, setApplyingId] = useState<number | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [opportunityError, setOpportunityError] = useState<string | null>(null);
	const [opportunityMessage, setOpportunityMessage] = useState<string | null>(
		null,
	);
	const [applicationNoteDrafts, setApplicationNoteDrafts] = useState<
		Record<number, string>
	>({});
	const [opportunityNoteDrafts, setOpportunityNoteDrafts] = useState<
		Record<number, string>
	>({});
	const [savingApplicationId, setSavingApplicationId] = useState<number | null>(
		null,
	);
	const showLongWaitHint = useDelayedFlag(loading || generating, 7000);

	useEffect(() => {
		const stored = getStoredProfileId();
		const id = stored ? Number(stored) : null;
		setProfileId(id && Number.isFinite(id) ? id : null);
	}, []);

	useEffect(() => {
		async function load() {
			if (!profileId) {
				setLoading(false);
				return;
			}
			setLoading(true);
			setError(null);
			try {
				setData(await getInternshipReadiness(profileId));
			} catch {
				setData(null);
			} finally {
				setLoading(false);
			}
		}
		void load();
	}, [profileId]);

	const loadOpportunityBoard = useCallback(
		async function loadOpportunityBoard(showLoader = true) {
			if (!profileId) {
				setOpportunities([]);
				setManagedInternships([]);
				setApplications([]);
				setPlacementActivity([]);
				setUpcomingActions([]);
				setApplicationNoteDrafts({});
				return;
			}
			if (showLoader) setOpportunityLoading(true);
			setOpportunityError(null);
			try {
				const [
					opportunityResult,
					applicationResult,
					activityResult,
					upcomingResult,
					managedInternshipResult,
				] = await Promise.all([
					listStudentPlacementOpportunities(profileId),
					listStudentPlacementApplications(profileId),
					listStudentPlacementActivity(profileId, 8),
					listStudentPlacementUpcomingActions(profileId, 8),
					listManagedInternshipOpportunities(profileId),
				]);
				setOpportunities(opportunityResult.items);
				setManagedInternships(managedInternshipResult.items);
				setApplications(applicationResult.items);
				setPlacementActivity(activityResult.items);
				setUpcomingActions(upcomingResult.items);
				setApplicationNoteDrafts(
					Object.fromEntries(
						applicationResult.items.map((application) => [
							application.id,
							application.interest_note ?? "",
						]),
					),
				);
			} catch (err) {
				setOpportunities([]);
				setManagedInternships([]);
				setApplications([]);
				setPlacementActivity([]);
				setUpcomingActions([]);
				setApplicationNoteDrafts({});
				setOpportunityError(
					err instanceof Error
						? err.message
						: "Placement opportunities could not load.",
				);
			} finally {
				if (showLoader) setOpportunityLoading(false);
			}
		},
		[profileId],
	);

	useEffect(() => {
		void loadOpportunityBoard();
	}, [loadOpportunityBoard]);

	async function handleGenerate() {
		if (!profileId) return;
		setGenerating(true);
		setError(null);
		try {
			setData(await generateInternshipReadiness(profileId));
		} catch (err) {
			const message =
				err instanceof Error ? err.message : "Failed to generate readiness.";
			setError(toGentleAiMessage(message));
		} finally {
			setGenerating(false);
		}
	}

	async function handleApply(
		opportunityId: number,
		status: "interested" | "applied",
	) {
		if (!profileId) return;
		setApplyingId(opportunityId);
		setOpportunityError(null);
		setOpportunityMessage(null);
		try {
			await applyToPlacementOpportunity(opportunityId, {
				profile_id: profileId,
				status,
				interest_note: opportunityNoteDrafts[opportunityId]?.trim() || null,
			});
			await loadOpportunityBoard(false);
			setOpportunityNoteDrafts((drafts) => {
				const next = { ...drafts };
				delete next[opportunityId];
				return next;
			});
			setOpportunityMessage(
				status === "applied"
					? "Application marked for this opportunity."
					: "Interest marked for this opportunity.",
			);
		} catch (err) {
			setOpportunityError(
				err instanceof Error ? err.message : "Opportunity action failed.",
			);
		} finally {
			setApplyingId(null);
		}
	}

	async function handleApplicationUpdate(
		application: PlacementApplicationRead,
		status: "interested" | "applied" | "withdrawn",
	) {
		setSavingApplicationId(application.id);
		setOpportunityError(null);
		setOpportunityMessage(null);
		try {
			await updateStudentPlacementApplication(application.id, {
				status,
				interest_note: applicationNoteDrafts[application.id]?.trim() || null,
			});
			await loadOpportunityBoard(false);
			setOpportunityMessage(
				status === "withdrawn"
					? "Application withdrawn."
					: status === "applied"
						? "Application marked as applied."
						: "Application note updated.",
			);
		} catch (err) {
			setOpportunityError(
				err instanceof Error ? err.message : "Application update failed.",
			);
		} finally {
			setSavingApplicationId(null);
		}
	}

	return (
		<PageShell>
			<PageHeader
				title="Internship readiness"
				description="Turn projects, skill gaps, and experience signals into credible placement evidence."
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
					<div className="h-24 animate-pulse rounded-lg bg-zinc-100" />
				</GlassPanel>
			) : null}

			{(loading || generating) && showLongWaitHint ? (
				<Notice title="Still working" description={LONG_WAIT_NOTICE} />
			) : null}

			{error ? (
				<Notice
					title="Readiness could not update"
					description={error}
					tone="danger"
				/>
			) : null}

			{opportunityError ? (
				<Notice
					title="Opportunities could not update"
					description={opportunityError}
					tone="danger"
				/>
			) : null}

			{opportunityMessage ? (
				<Notice title="Opportunity updated" description={opportunityMessage} />
			) : null}

			{!profileId ? (
				<EmptyState
					title="Create a profile first"
					description="Internship guidance needs your academic path, target industry, skills, and project history."
					action={
						<Link
							href="/create-profile"
							className={buttonClass({ variant: "primary" })}
						>
							Create profile
						</Link>
					}
				/>
			) : null}

			{profileId && !loading && !data ? (
				<EmptyState
					title="No internship readiness score yet"
					description="Generate a focused action loop for the evidence you should build before applying."
					action={
						<button
							type="button"
							onClick={handleGenerate}
							disabled={generating}
							className={buttonClass({ variant: "primary" })}
						>
							{generating ? "Generating..." : "Generate readiness"}
						</button>
					}
				/>
			) : null}

			{data ? (
				<>
					<div className="grid gap-4 md:grid-cols-3">
						<MetricTile
							label="Readiness score"
							value={data.readiness_score}
							helper="Project, skill, and experience fit."
							tone={LEVEL_TONES[data.readiness_level] ?? "neutral"}
							statusLabel={data.readiness_level}
						/>
						<MetricTile
							label="Action items"
							value={data.action_plan.length}
							helper="Top actions to improve evidence."
							tone="orange"
						/>
						<MetricTile
							label="Dashboard loop"
							value="Active"
							helper="Use this page with resume and training."
							tone="dark"
						/>
					</div>

					<div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
						<GlassPanel className="space-y-5">
							<div className="flex items-center justify-between gap-3">
								<div>
									<h2 className="text-lg font-semibold text-zinc-950">
										Current signal
									</h2>
									<p className="mt-1 text-sm text-zinc-600">
										Use this as the bridge between training, resume, and
										placement readiness.
									</p>
								</div>
								<StatusBadge
									tone={LEVEL_TONES[data.readiness_level] ?? "neutral"}
								>
									{data.readiness_level}
								</StatusBadge>
							</div>
							<ScoreBar
								value={data.readiness_score}
								label="Internship readiness"
							/>
							<button
								type="button"
								onClick={handleGenerate}
								disabled={generating}
								className={buttonClass({ variant: "secondary" })}
							>
								{generating ? "Refreshing..." : "Recalculate"}
							</button>
						</GlassPanel>

						<GlassPanel>
							<h2 className="text-lg font-semibold text-zinc-950">
								Next internship actions
							</h2>
							<p className="mt-1 text-sm text-zinc-600">
								Complete these before applying so your resume has stronger
								proof, not just claims.
							</p>
							<div className="mt-4">
								<CompactActionList
									items={data.action_plan}
									emptyText="No internship actions returned yet."
									limit={6}
								/>
							</div>
							<div className="mt-5 flex flex-wrap gap-2">
								<Link
									href="/resume"
									className={buttonClass({ variant: "secondary" })}
								>
									Update resume
								</Link>
								<Link
									href="/training"
									className={buttonClass({ variant: "secondary" })}
								>
									Close skill gaps
								</Link>
							</div>
						</GlassPanel>
					</div>
				</>
			) : null}

			{profileId ? (
				<GlassPanel className="grid gap-5 lg:grid-cols-2">
					<div>
						<div className="flex flex-wrap items-start justify-between gap-3">
							<div>
								<h2 className="text-lg font-semibold text-zinc-950">
									Upcoming placement actions
								</h2>
								<p className="mt-1 text-sm leading-6 text-zinc-600">
									Your interviews, next steps, deadlines, and joining dates in
									one place.
								</p>
							</div>
							<StatusBadge tone={upcomingActions.length ? "orange" : "neutral"}>
								{upcomingActions.length} scheduled
							</StatusBadge>
						</div>
						<div className="mt-4 divide-y divide-black/10 rounded-xl border border-black/10 bg-white/70">
							{upcomingActions.length ? (
								upcomingActions.slice(0, 5).map((action) => {
									const label = buildStudentPlacementActionLabel(action);
									return (
										<div
											key={`${action.action_type}-${action.application_id ?? action.opportunity_id ?? action.interview_round_id}-${action.due_at}`}
											className="grid gap-2 p-3 sm:grid-cols-[1fr_auto] sm:items-center"
										>
											<div>
												<p className="text-sm font-semibold text-zinc-950">
													{label.title}
												</p>
												<p className="mt-1 text-xs leading-5 text-zinc-500">
													{label.context}
												</p>
											</div>
											<p className="text-xs font-semibold text-zinc-700">
												{label.when}
											</p>
										</div>
									);
								})
							) : (
								<EmptyState
									title="No scheduled placement actions"
									description="When the placement cell assigns next steps, interviews, or offer dates, they appear here."
								/>
							)}
						</div>
					</div>

					<div>
						<div className="flex flex-wrap items-start justify-between gap-3">
							<div>
								<h2 className="text-lg font-semibold text-zinc-950">
									Recent placement updates
								</h2>
								<p className="mt-1 text-sm leading-6 text-zinc-600">
									A short trail of your application, interview, and offer
									changes.
								</p>
							</div>
							<StatusBadge tone="neutral">
								{placementActivity.length} recent
							</StatusBadge>
						</div>
						<div className="mt-4 divide-y divide-black/10 rounded-xl border border-black/10 bg-white/70">
							{placementActivity.length ? (
								placementActivity.slice(0, 5).map((item) => (
									<div
										key={item.id}
										className="grid gap-2 p-3 sm:grid-cols-[1fr_auto] sm:items-center"
									>
										<div>
											<p className="text-sm font-semibold text-zinc-950">
												{item.title}
											</p>
											<p className="mt-1 text-xs leading-5 text-zinc-500">
												{[item.opportunity_title, item.opportunity_company]
													.filter(Boolean)
													.join(" - ") || "Placement update"}
											</p>
										</div>
										<p className="text-xs font-semibold text-zinc-700">
											{formatDate(item.created_at)}
										</p>
									</div>
								))
							) : (
								<EmptyState
									title="No placement updates yet"
									description="Updates appear once you apply or the placement cell changes your application."
								/>
							)}
						</div>
					</div>
				</GlassPanel>
			) : null}

			{profileId ? (
				<GlassPanel className="space-y-4">
					<div className="flex flex-wrap items-start justify-between gap-3">
						<div>
							<h2 className="text-lg font-semibold text-zinc-950">
								Institution internship catalog
							</h2>
							<p className="mt-1 text-sm text-zinc-600">
								Admin-managed internships, labs, and experiential opportunities
								that build evidence for placements.
							</p>
						</div>
						<StatusBadge
							tone={managedInternships.length ? "orange" : "neutral"}
						>
							{managedInternships.length} listed
						</StatusBadge>
					</div>
					{managedInternships.length ? (
						<div className="grid gap-3 md:grid-cols-2">
							{managedInternships.map((item) => (
								<div
									key={item.id}
									className="rounded-xl border border-black/10 bg-white/70 p-4"
								>
									<div className="flex flex-wrap items-center gap-2">
										<h3 className="font-semibold text-zinc-950">
											{item.title}
										</h3>
										{item.company ? (
											<StatusBadge tone="neutral">{item.company}</StatusBadge>
										) : null}
									</div>
									<p className="mt-2 text-sm leading-6 text-zinc-600">
										{item.summary ||
											"Use this opportunity to build project, communication, and workplace readiness evidence."}
									</p>
									<div className="mt-3 flex flex-wrap gap-2">
										{[item.duration, item.location, item.deadline]
											.filter(Boolean)
											.map((meta) => (
												<span
													key={meta}
													className="rounded-full border border-black/10 bg-white px-2.5 py-1 text-xs font-semibold text-zinc-600"
												>
													{meta}
												</span>
											))}
										{item.skills.map((skill) => (
											<span
												key={skill}
												className="rounded-full border border-orange-200 bg-orange-50 px-2.5 py-1 text-xs font-semibold text-orange-800"
											>
												{skill}
											</span>
										))}
									</div>
									{item.eligibility.length ? (
										<div className="mt-3 rounded-xl border border-black/10 bg-white p-3">
											<p className="text-xs font-semibold text-zinc-700">
												Eligibility
											</p>
											<ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-5 text-zinc-600">
												{item.eligibility.map((rule) => (
													<li key={rule}>{rule}</li>
												))}
											</ul>
										</div>
									) : null}
									{item.apply_url ? (
										<a
											href={item.apply_url}
											target="_blank"
											rel="noreferrer"
											className={buttonClass({
												variant: "secondary",
												className: "mt-4 min-h-9 px-3 py-1 text-xs",
											})}
										>
											Open application
										</a>
									) : null}
								</div>
							))}
						</div>
					) : (
						<EmptyState
							title="No institution internships listed yet"
							description="Admin-managed internship catalog entries will appear here after the institution publishes them."
						/>
					)}
				</GlassPanel>
			) : null}

			{profileId ? (
				<GlassPanel className="space-y-4">
					<div className="flex flex-wrap items-start justify-between gap-3">
						<div>
							<h2 className="text-lg font-semibold text-zinc-950">
								My applications
							</h2>
							<p className="mt-1 text-sm text-zinc-600">
								Track the drives you marked from this readiness loop and use
								status changes to plan your next action.
							</p>
						</div>
						<StatusBadge tone="neutral">
							{applications.length} tracked
						</StatusBadge>
					</div>
					{opportunityLoading ? (
						<div className="h-16 animate-pulse rounded-lg bg-zinc-100" />
					) : null}
					{!opportunityLoading && applications.length === 0 ? (
						<EmptyState
							title="No applications tracked yet"
							description="Mark interest or apply from matched opportunities to keep your placement history visible here."
						/>
					) : null}
					{applications.length ? (
						<div className="divide-y divide-black/10 rounded-xl border border-black/10 bg-white/70">
							{applications.map((application) => {
								const canEditNote = canStudentEditApplicationNote(
									application.status,
								);
								const canWithdraw = canStudentWithdrawApplication(
									application.status,
								);
								return (
									<div
										key={application.id}
										className="grid gap-4 p-4 lg:grid-cols-[1fr_260px] lg:items-start"
									>
										<div>
											<div className="flex flex-wrap items-center gap-2">
												<h3 className="font-semibold text-zinc-950">
													{application.opportunity_title ?? "Opportunity"}
												</h3>
												<StatusBadge tone="neutral">
													{application.opportunity_company ?? "Placement cell"}
												</StatusBadge>
												{application.opportunity_type ? (
													<StatusBadge tone="neutral">
														{application.opportunity_type}
													</StatusBadge>
												) : null}
											</div>
											<p className="mt-2 text-sm text-zinc-600">
												{buildApplicationNextStep(application.status)}
											</p>
											{application.next_step || application.next_step_due_at ? (
												<div className="mt-3 rounded-xl border border-orange-200 bg-orange-50/70 p-3">
													<p className="text-xs font-semibold text-orange-800">
														Placement-cell next step
													</p>
													<p className="mt-1 text-sm leading-6 text-zinc-800">
														{application.next_step ||
															"Watch for placement-cell instructions."}
													</p>
													{application.next_step_due_at ? (
														<p className="mt-1 text-xs font-semibold text-orange-800">
															Due {formatDateTime(application.next_step_due_at)}
														</p>
													) : null}
												</div>
											) : null}
											{application.offer_status ? (
												<div className="mt-3 rounded-xl border border-black/10 bg-white/80 p-3">
													<div className="flex flex-wrap items-center gap-2">
														<p className="text-xs font-semibold text-zinc-700">
															Offer outcome
														</p>
														<StatusBadge
															tone={offerTone(application.offer_status)}
														>
															{offerStatusLabel(application.offer_status)}
														</StatusBadge>
													</div>
													<p className="mt-2 text-sm font-semibold text-zinc-950">
														{application.offer_role ??
															application.opportunity_title ??
															"Offer role pending"}
													</p>
													<p className="mt-1 text-xs leading-5 text-zinc-600">
														{[
															application.offer_package,
															application.offer_location,
															application.offer_joining_date
																? `Joining ${formatDate(
																		application.offer_joining_date,
																	)}`
																: null,
														]
															.filter(Boolean)
															.join(" - ") ||
															"Placement cell will share details."}
													</p>
													{application.offer_notes ? (
														<p className="mt-2 text-xs leading-5 text-zinc-500">
															{application.offer_notes}
														</p>
													) : null}
												</div>
											) : null}
											{application.interview_rounds?.length ? (
												<div className="mt-3 rounded-xl border border-black/10 bg-white/80 p-3">
													<p className="text-xs font-semibold text-zinc-700">
														Interview schedule
													</p>
													<div className="mt-2 space-y-2">
														{application.interview_rounds.map((round) => (
															<div
																key={round.id}
																className="rounded-lg border border-black/10 bg-zinc-50 px-3 py-2 text-xs leading-5 text-zinc-600"
															>
																<div className="flex flex-wrap items-center gap-2">
																	<span className="font-semibold text-zinc-900">
																		{round.round_name}
																	</span>
																	<StatusBadge
																		tone={
																			round.status === "completed"
																				? "success"
																				: round.status === "cancelled"
																					? "danger"
																					: "orange"
																		}
																	>
																		{round.status}
																	</StatusBadge>
																</div>
																<p className="mt-1">
																	{round.scheduled_at
																		? formatDateTime(round.scheduled_at)
																		: "Schedule pending"}
																	{round.mode ? ` - ${round.mode}` : ""}
																</p>
																{round.location ? (
																	<p>{round.location}</p>
																) : null}
																{round.notes ? (
																	<p className="mt-1 text-zinc-500">
																		{round.notes}
																	</p>
																) : null}
															</div>
														))}
													</div>
												</div>
											) : null}
											<p className="mt-2 text-xs text-zinc-500">
												Tracked {formatDate(application.created_at)}
											</p>
											<div className="mt-3 grid gap-2 md:grid-cols-2">
												<label className="text-xs font-semibold text-zinc-600">
													Student note
													<textarea
														value={applicationNoteDrafts[application.id] ?? ""}
														onChange={(event) =>
															setApplicationNoteDrafts((drafts) => ({
																...drafts,
																[application.id]: event.target.value,
															}))
														}
														className="mt-1 min-h-20 w-full rounded-xl border border-black/10 bg-white px-3 py-2 text-sm font-normal text-zinc-900 outline-none transition focus:border-orange-500 focus:ring-2 focus:ring-orange-200"
														placeholder="Add resume links, availability, or preparation note."
														disabled={!canEditNote}
													/>
													{canEditNote ? null : (
														<span className="mt-1 block text-xs font-normal text-zinc-500">
															Notes are locked after the placement cell moves
															the application into review.
														</span>
													)}
												</label>
												<div className="rounded-xl border border-black/10 bg-white px-3 py-2">
													<p className="text-xs font-semibold text-zinc-600">
														Placement-cell note
													</p>
													<p className="mt-1 text-sm text-zinc-700">
														{application.admin_notes ||
															"No placement-cell note yet."}
													</p>
												</div>
											</div>
										</div>
										<div className="flex flex-wrap items-center gap-2 lg:flex-col lg:items-stretch">
											<StatusBadge tone={applicationTone(application.status)}>
												{application.status.replace("_", " ")}
											</StatusBadge>
											{canEditNote ? (
												<button
													type="button"
													onClick={() =>
														void handleApplicationUpdate(
															application,
															application.status === "applied"
																? "applied"
																: "interested",
														)
													}
													disabled={savingApplicationId === application.id}
													className={buttonClass({
														variant: "secondary",
														className: "min-h-9 px-3 py-1 text-xs",
													})}
												>
													Save note
												</button>
											) : null}
											{application.status === "interested" ? (
												<button
													type="button"
													onClick={() =>
														void handleApplicationUpdate(application, "applied")
													}
													disabled={savingApplicationId === application.id}
													className={buttonClass({
														variant: "primary",
														className: "min-h-9 px-3 py-1 text-xs",
													})}
												>
													Mark applied
												</button>
											) : null}
											{canWithdraw ? (
												<button
													type="button"
													onClick={() =>
														void handleApplicationUpdate(
															application,
															"withdrawn",
														)
													}
													disabled={savingApplicationId === application.id}
													className={buttonClass({
														variant: "secondary",
														className: "min-h-9 px-3 py-1 text-xs",
													})}
												>
													Withdraw
												</button>
											) : null}
										</div>
									</div>
								);
							})}
						</div>
					) : null}
				</GlassPanel>
			) : null}

			{profileId ? (
				<GlassPanel className="space-y-4">
					<div className="flex flex-wrap items-start justify-between gap-3">
						<div>
							<h2 className="text-lg font-semibold text-zinc-950">
								Matched opportunities
							</h2>
							<p className="mt-1 text-sm text-zinc-600">
								These openings come from the institution placement board and are
								matched against your profile signals.
							</p>
						</div>
						<StatusBadge tone="orange">
							{opportunities.length} available
						</StatusBadge>
					</div>
					{opportunityLoading ? (
						<div className="h-20 animate-pulse rounded-lg bg-zinc-100" />
					) : null}
					{!opportunityLoading && opportunities.length === 0 ? (
						<EmptyState
							title="No matched opportunities yet"
							description="Check back after the placement cell publishes internships or placement drives for your profile."
						/>
					) : null}
					<div className="grid gap-3">
						{opportunities.map((opportunity) => {
							const meta = buildOpportunityMeta(opportunity);
							const matchReasons = buildMatchReasons(opportunity);
							const isTracked = Boolean(opportunity.application_status);
							return (
								<div
									key={opportunity.id}
									className="rounded-xl border border-black/10 bg-white/70 p-4"
								>
									<div className="grid gap-4 lg:grid-cols-[1fr_280px]">
										<div>
											<div className="flex flex-wrap items-center gap-2">
												<h3 className="font-semibold text-zinc-950">
													{opportunity.title}
												</h3>
												<StatusBadge tone="neutral">
													{opportunity.company}
												</StatusBadge>
												{opportunity.application_status ? (
													<StatusBadge tone="success">
														{opportunity.application_status.replace("_", " ")}
													</StatusBadge>
												) : null}
											</div>
											{meta.length ? (
												<div className="mt-2 flex flex-wrap gap-2">
													{meta.map((item) => (
														<span
															key={item}
															className="rounded-full border border-black/10 bg-white px-2.5 py-1 text-xs font-semibold text-zinc-600"
														>
															{item}
														</span>
													))}
												</div>
											) : null}
											<p className="mt-3 text-sm leading-6 text-zinc-600">
												{opportunity.description ||
													"Review the match reasons and decide whether this fits your next readiness step."}
											</p>
											{matchReasons.length ? (
												<div className="mt-3 rounded-xl border border-orange-200 bg-orange-50/70 p-3">
													<p className="text-xs font-semibold text-orange-700">
														Why this appears for you
													</p>
													<div className="mt-2 flex flex-wrap gap-2">
														{matchReasons.map((reason) => (
															<span
																key={reason}
																className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-zinc-700"
															>
																{reason}
															</span>
														))}
													</div>
												</div>
											) : null}
										</div>
										<div className="space-y-3 rounded-xl border border-black/10 bg-white p-3">
											<label className="block text-xs font-semibold text-zinc-600">
												Application note
												<textarea
													value={opportunityNoteDrafts[opportunity.id] ?? ""}
													onChange={(event) =>
														setOpportunityNoteDrafts((drafts) => ({
															...drafts,
															[opportunity.id]: event.target.value,
														}))
													}
													className="mt-1 min-h-20 w-full rounded-xl border border-black/10 bg-white px-3 py-2 text-sm font-normal text-zinc-900 outline-none transition focus:border-orange-500 focus:ring-2 focus:ring-orange-200 disabled:bg-zinc-50"
													placeholder="Add availability, resume link, or fit note."
													disabled={isTracked}
												/>
											</label>
											<div className="flex flex-wrap gap-2">
												<button
													type="button"
													onClick={() =>
														void handleApply(opportunity.id, "interested")
													}
													disabled={applyingId === opportunity.id || isTracked}
													className={buttonClass({
														variant: "secondary",
														className: "min-h-9 px-3 py-1 text-xs",
													})}
												>
													Interested
												</button>
												<button
													type="button"
													onClick={() =>
														void handleApply(opportunity.id, "applied")
													}
													disabled={applyingId === opportunity.id || isTracked}
													className={buttonClass({
														variant: "primary",
														className: "min-h-9 px-3 py-1 text-xs",
													})}
												>
													Apply
												</button>
												{opportunity.apply_url ? (
													<a
														href={opportunity.apply_url}
														target="_blank"
														rel="noreferrer"
														className={buttonClass({
															variant: "secondary",
															className: "min-h-9 px-3 py-1 text-xs",
														})}
													>
														External form
													</a>
												) : null}
											</div>
											<p className="text-xs leading-5 text-zinc-500">
												{isTracked
													? "Already tracked in My applications."
													: "This action records your placement-cell trail inside your workspace."}
											</p>
										</div>
									</div>
								</div>
							);
						})}
					</div>
				</GlassPanel>
			) : null}
		</PageShell>
	);
}

function formatDate(value: string) {
	return new Intl.DateTimeFormat("en-IN", {
		day: "2-digit",
		month: "short",
		year: "numeric",
	}).format(new Date(value));
}

function formatDateTime(value: string) {
	return new Intl.DateTimeFormat("en-IN", {
		day: "2-digit",
		month: "short",
		hour: "2-digit",
		minute: "2-digit",
	}).format(new Date(value));
}

function applicationTone(
	status: PlacementApplicationRead["status"],
): "success" | "warning" | "danger" | "neutral" | "orange" {
	if (
		status === "placed" ||
		status === "joined" ||
		status === "offer_made" ||
		status === "shortlisted"
	) {
		return "success";
	}
	if (status === "applied" || status === "interview_scheduled") return "orange";
	if (status === "not_selected" || status === "withdrawn") return "danger";
	if (status === "interested" || status === "screening") return "warning";
	return "neutral";
}

function offerStatusLabel(
	status: NonNullable<PlacementApplicationRead["offer_status"]>,
) {
	switch (status) {
		case "offered":
			return "Offered";
		case "accepted":
			return "Accepted";
		case "declined":
			return "Declined";
		case "withdrawn":
			return "Withdrawn";
		default:
			return "Offer";
	}
}

function offerTone(
	status: NonNullable<PlacementApplicationRead["offer_status"]>,
): "success" | "warning" | "danger" | "neutral" | "orange" {
	if (status === "accepted") return "success";
	if (status === "offered") return "orange";
	return "danger";
}
