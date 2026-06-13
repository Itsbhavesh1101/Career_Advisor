"use client";

import { useRouter } from "next/navigation";
import { use, useCallback, useEffect, useRef, useState } from "react";

import InsightPanel from "@/components/InsightPanel";
import ProgressBar from "@/components/ProgressBar";
import QuestionCard from "@/components/QuestionCard";
import { buttonClass, Notice, PageHeader, PageShell } from "@/components/ui";
import {
	generateAnalysis,
	getJobStatus,
	getPsychometricQuizStatus,
	type PsychometricSessionStatusRead,
	reportPsychometricQuizAbandonment,
	startPsychometricQuiz,
	submitPsychometricAnswer,
} from "@/lib/api";

type QuizPageProps = {
	params: Promise<{ profileId: string }>;
};

const sessionKey = (profileId: number) => `psychometric_session_${profileId}`;
const MAX_RECORDED_RESPONSE_MS = 300000;

function randomId(): string {
	if (
		typeof crypto !== "undefined" &&
		typeof crypto.randomUUID === "function"
	) {
		return crypto.randomUUID();
	}
	return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export default function QuizPage({ params }: QuizPageProps) {
	const { profileId } = use(params);
	const numericProfileId = Number(profileId);
	const router = useRouter();

	const [session, setSession] = useState<PsychometricSessionStatusRead | null>(
		null,
	);
	const [loading, setLoading] = useState(true);
	const [answering, setAnswering] = useState(false);
	const [finalizing, setFinalizing] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
	const [analysisMessage, setAnalysisMessage] = useState<string | null>(null);

	const questionShownAtRef = useRef<number>(Date.now());
	const prefetchLockRef = useRef(false);
	const latestSessionRef = useRef<PsychometricSessionStatusRead | null>(null);
	const finalizingRef = useRef(false);
	const abandonmentSentRef = useRef<string | null>(null);

	useEffect(() => {
		latestSessionRef.current = session;
	}, [session]);

	useEffect(() => {
		finalizingRef.current = finalizing;
	}, [finalizing]);

	useEffect(() => {
		if (session?.current_question?.id) {
			questionShownAtRef.current = Date.now();
			setSelectedOptionId(null);
		}
	}, [session?.current_question?.id]);

	useEffect(() => {
		let mounted = true;

		async function loadSession() {
			if (Number.isNaN(numericProfileId)) {
				setError("Invalid profile ID.");
				setLoading(false);
				return;
			}

			setLoading(true);
			setError(null);
			try {
				const storedSessionId = localStorage.getItem(
					sessionKey(numericProfileId),
				);
				let nextSession: PsychometricSessionStatusRead;

				if (storedSessionId) {
					nextSession = await getPsychometricQuizStatus(storedSessionId);
				} else {
					const started = await startPsychometricQuiz(numericProfileId);
					nextSession = started.session;
					localStorage.setItem(
						sessionKey(numericProfileId),
						nextSession.session_id,
					);
				}

				if (!mounted) return;
				localStorage.setItem(
					sessionKey(numericProfileId),
					nextSession.session_id,
				);
				setSession(nextSession);
			} catch (err) {
				if (!mounted) return;
				setError(err instanceof Error ? err.message : "Failed to start quiz.");
			} finally {
				if (mounted) {
					setLoading(false);
				}
			}
		}

		void loadSession();
		return () => {
			mounted = false;
		};
	}, [numericProfileId]);

	async function finalizeAndRedirect() {
		if (Number.isNaN(numericProfileId)) return;

		finalizingRef.current = true;
		setFinalizing(true);
		setAnalysisMessage("Building your career analysis...");
		setError(null);
		try {
			const dispatch = await generateAnalysis(numericProfileId);
			if (dispatch.status === "failed") {
				throw new Error("Analysis generation failed. Please retry.");
			}
			await waitForAnalysisJob(dispatch.job_id);
			localStorage.removeItem(sessionKey(numericProfileId));
			router.push(`/analysis/${numericProfileId}`);
		} catch (err) {
			finalizingRef.current = false;
			setFinalizing(false);
			setAnalysisMessage(null);
			setError(
				err instanceof Error
					? err.message
					: "Analysis generation failed. Please retry.",
			);
		}
	}

	async function waitForAnalysisJob(jobId: string) {
		const timeoutMs = 2 * 60 * 1000;
		const pollIntervalMs = 1500;
		const start = Date.now();

		while (Date.now() - start < timeoutMs) {
			const envelope = await getJobStatus(jobId);
			const job = envelope.job;
			setAnalysisMessage(
				job.message || `Preparing analysis (${job.progress}%)`,
			);

			if (job.status === "completed") {
				return;
			}
			if (job.status === "failed") {
				throw new Error(
					job.message || "Analysis generation failed. Please retry.",
				);
			}

			await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
		}

		throw new Error(
			"Analysis is taking longer than expected. Please retry in a moment.",
		);
	}

	async function prefetchStatus() {
		if (!session || prefetchLockRef.current) return;
		prefetchLockRef.current = true;
		try {
			const latest = await getPsychometricQuizStatus(session.session_id);
			setSession(latest);
		} catch {
			// Prefetch is best-effort.
		} finally {
			prefetchLockRef.current = false;
		}
	}

	const reportAbandonment = useCallback((reason: string) => {
		const active = latestSessionRef.current;
		if (!active) return;
		if (finalizingRef.current) return;
		if (active.status !== "queued" && active.status !== "in_progress") return;
		if (abandonmentSentRef.current === active.session_id) return;

		abandonmentSentRef.current = active.session_id;
		void reportPsychometricQuizAbandonment(active.session_id, reason).catch(
			() => {
				abandonmentSentRef.current = null;
			},
		);
	}, []);

	useEffect(() => {
		const onBeforeUnload = () => {
			reportAbandonment("before_unload");
		};

		const onPageHide = () => {
			reportAbandonment("page_hide");
		};

		window.addEventListener("beforeunload", onBeforeUnload);
		window.addEventListener("pagehide", onPageHide);

		return () => {
			window.removeEventListener("beforeunload", onBeforeUnload);
			window.removeEventListener("pagehide", onPageHide);
			reportAbandonment("route_change");
		};
	}, [reportAbandonment]);

	async function handleSelect(optionId: string) {
		if (!session || !session.current_question) return;
		setError(null);
		setSelectedOptionId(optionId);
		setAnswering(true);

		try {
			const responseMs = Math.min(
				Math.max(Date.now() - questionShownAtRef.current, 0),
				MAX_RECORDED_RESPONSE_MS,
			);
			const result = await submitPsychometricAnswer(session.session_id, {
				question_id: session.current_question.id,
				option_id: optionId,
				answer_id: randomId(),
				idempotency_key: `${session.current_question.id}:${optionId}`,
				response_ms: responseMs,
			});
			latestSessionRef.current = result.session;
			setSession(result.session);

			if (result.session.status === "completed") {
				await finalizeAndRedirect();
				return;
			}

			void prefetchStatus();
		} catch (err) {
			setSelectedOptionId(null);
			setError(err instanceof Error ? err.message : "Unable to submit answer.");
		} finally {
			setAnswering(false);
		}
	}

	if (loading) {
		return (
			<PageShell className="flex min-h-[420px] items-center justify-center">
				<div className="rounded-xl border border-black/10 bg-white px-8 py-7 text-center shadow-lg">
					<div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
					<p className="mt-4 text-sm font-medium text-zinc-950">
						Preparing your adaptive quiz
					</p>
					<p className="mt-1 text-xs text-zinc-500">
						Calibrating the first career signal...
					</p>
				</div>
			</PageShell>
		);
	}

	if (error && !session) {
		return (
			<PageShell className="max-w-4xl">
				<Notice
					title="Quiz could not start"
					description={error}
					tone="danger"
				/>
			</PageShell>
		);
	}

	if (!session) {
		return (
			<PageShell className="max-w-4xl">
				<Notice title="No active quiz session found" tone="warning" />
			</PageShell>
		);
	}

	if (session.status === "completed" || !session.current_question) {
		return (
			<PageShell className="max-w-4xl">
				<PageHeader
					title="Quiz completed"
					description="Your answers are ready for analysis."
					className="border-b-0 pb-0"
				/>
				<p className="text-sm text-zinc-600">
					Great work. We are preparing your analysis dashboard before moving
					ahead.
				</p>
				{analysisMessage ? (
					<p className="text-sm text-zinc-600">{analysisMessage}</p>
				) : null}
				{error ? (
					<Notice
						title="Analysis could not finalize"
						description={error}
						tone="danger"
					/>
				) : null}
				<button
					type="button"
					onClick={() => void finalizeAndRedirect()}
					disabled={finalizing}
					className={buttonClass()}
				>
					{finalizing ? "Preparing analysis..." : "Continue to Analysis"}
				</button>
			</PageShell>
		);
	}

	return (
		<PageShell className="grid gap-6 lg:grid-cols-[2fr_1fr]">
			<section className="space-y-4">
				<div className="space-y-2">
					<div className="inline-flex rounded-full border border-orange-200 bg-orange-50 px-3 py-1 text-xs font-semibold text-orange-800">
						{session.ai_status === "ai_generated"
							? "Live AI pathing"
							: "Guided adaptive pathing"}
					</div>
					<h1 className="text-3xl font-semibold tracking-tight text-zinc-950">
						Adaptive Career Quiz
					</h1>
					<p className="max-w-2xl text-sm leading-6 text-zinc-600">
						Answer one question at a time. The quiz recalibrates focus,
						confidence, and branch-fit signals after each response.
					</p>
				</div>
				<ProgressBar
					answered={session.questions_answered}
					minQuestions={session.min_questions}
					maxQuestions={session.max_questions}
					confidence={session.confidence}
				/>
				{error ? (
					<Notice
						title="Answer was not saved"
						description={error}
						tone="danger"
					/>
				) : null}
				<QuestionCard
					question={session.current_question}
					onSelect={handleSelect}
					disabled={answering}
					selectedOptionId={selectedOptionId}
					isAdvancing={answering}
				/>
			</section>
			<InsightPanel
				traits={session.current_traits}
				aiStatus={session.ai_status}
				adaptationReason={session.adaptation_reason}
				nextFocus={session.next_focus}
			/>
		</PageShell>
	);
}
