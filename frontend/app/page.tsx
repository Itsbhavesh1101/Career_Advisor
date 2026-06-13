"use client";

import {
	ArrowRight,
	BookOpenCheck,
	Bot,
	BrainCircuit,
	BriefcaseBusiness,
	ClipboardCheck,
	FileText,
	GraduationCap,
	MessagesSquare,
	Route,
	ShieldCheck,
	Sparkles,
	UserRoundCheck,
} from "lucide-react";
import Link from "next/link";
import { type ComponentType, useEffect, useState } from "react";
import { buttonClass, cn, GlassPanel, StatusBadge } from "@/components/ui";
import { brandInitials, useBranding } from "@/lib/branding";
import { getStoredProfileId, hasStoredSessionHint } from "@/lib/profile";

type GatewayPathProps = {
	title: string;
	description: string;
	href: string;
	action: string;
	icon: ComponentType<{ className?: string }>;
	emphasis?: "primary" | "dark";
	meta: string;
};

type FeatureItem = {
	title: string;
	description: string;
	icon: ComponentType<{ className?: string }>;
	tone?: "orange" | "dark";
};

const features: FeatureItem[] = [
	{
		title: "Adaptive quiz",
		description:
			"Student intake captures interests, strengths, confidence, and readiness signals.",
		icon: ClipboardCheck,
		tone: "orange",
	},
	{
		title: "AI guidance",
		description:
			"Recommendations connect branch fit or career paths to concrete next actions.",
		icon: BrainCircuit,
	},
	{
		title: "Personalized copilot",
		description:
			"Students get a guided assistant that keeps recommendations tied to their profile and next step.",
		icon: MessagesSquare,
	},
	{
		title: "Resume readiness",
		description:
			"College students can turn resume gaps into placement evidence.",
		icon: FileText,
	},
	{
		title: "Training actions",
		description:
			"Weak skills and demand signals become focused training priorities.",
		icon: BookOpenCheck,
	},
	{
		title: "Internship readiness",
		description:
			"Projects, skills, and experience signals become practical application steps.",
		icon: BriefcaseBusiness,
	},
];

const branchSteps = ["Profile", "Quiz", "Program guidance", "Decision plan"];
const placementSteps = [
	"Profile",
	"Quiz",
	"Career analysis",
	"Readiness actions",
];

function GatewayPath({
	title,
	description,
	href,
	action,
	icon: Icon,
	emphasis = "primary",
	meta,
}: GatewayPathProps) {
	const isPrimary = emphasis === "primary";

	return (
		<GlassPanel
			as="article"
			className={cn(
				"group grid gap-2 !p-3 transition hover:-translate-y-0.5 hover:border-orange-300/70 sm:flex sm:h-full sm:flex-col sm:justify-between sm:gap-5 sm:!p-5",
				isPrimary ? "ring-1 ring-orange-200" : "",
			)}
		>
			<div>
				<div className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-start gap-3 sm:flex sm:items-start sm:justify-between sm:gap-4">
					<div
						className={cn(
							"flex h-9 w-9 items-center justify-center rounded-xl sm:h-12 sm:w-12",
							isPrimary ? "bg-orange-500 text-white" : "bg-zinc-950 text-white",
						)}
					>
						<Icon className="h-5 w-5" />
					</div>
					<h2 className="text-base font-semibold tracking-tight text-zinc-950 sm:hidden">
						{title}
					</h2>
					<StatusBadge tone={isPrimary ? "orange" : "dark"}>{meta}</StatusBadge>
				</div>
				<h2 className="mt-5 hidden text-xl font-semibold tracking-tight text-zinc-950 sm:block">
					{title}
				</h2>
				<p className="max-h-5 overflow-hidden text-sm leading-5 text-zinc-600 sm:mt-2 sm:max-h-none sm:leading-6">
					{description}
				</p>
			</div>
			<Link
				href={href}
				className={buttonClass({
					variant: isPrimary ? "primary" : "dark",
					className:
						"!min-h-9 w-fit px-3 py-1.5 text-xs sm:min-h-10 sm:px-4 sm:py-2 sm:text-sm",
				})}
			>
				{action}
				<ArrowRight className="ml-2 h-4 w-4" />
			</Link>
		</GlassPanel>
	);
}

function FeatureCard({ title, description, icon: Icon, tone }: FeatureItem) {
	const strong = tone === "orange" || tone === "dark";
	return (
		<div className="rounded-xl border border-black/10 bg-white p-4 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
			<div
				className={cn(
					"flex h-10 w-10 items-center justify-center rounded-lg",
					tone === "orange"
						? "bg-orange-500 text-white"
						: tone === "dark"
							? "bg-zinc-950 text-white"
							: "bg-zinc-100 text-zinc-800",
				)}
			>
				<Icon className="h-5 w-5" />
			</div>
			<h3 className="mt-4 text-base font-semibold text-zinc-950">{title}</h3>
			<p className="mt-2 text-sm leading-6 text-zinc-600">{description}</p>
			{strong ? (
				<div className="mt-4 h-1 w-10 rounded-full bg-orange-500" />
			) : null}
		</div>
	);
}

function WorkflowBand({
	title,
	description,
	steps,
	tone = "orange",
}: {
	title: string;
	description: string;
	steps: string[];
	tone?: "orange" | "dark";
}) {
	return (
		<GlassPanel className="p-5">
			<div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
				<div className="max-w-lg">
					<h3 className="text-lg font-semibold text-zinc-950">{title}</h3>
					<p className="mt-2 text-sm leading-6 text-zinc-600">{description}</p>
				</div>
				<div className="flex flex-wrap gap-2">
					{steps.map((step, index) => (
						<div
							key={step}
							className="flex items-center gap-2 rounded-full border border-black/10 bg-white px-3 py-2 text-sm font-semibold text-zinc-700"
						>
							<span
								className={cn(
									"flex h-6 w-6 items-center justify-center rounded-full text-xs text-white",
									tone === "orange" ? "bg-orange-500" : "bg-zinc-950",
								)}
							>
								{index + 1}
							</span>
							{step}
						</div>
					))}
				</div>
			</div>
		</GlassPanel>
	);
}

export default function HomePage() {
	const [savedProfileId, setSavedProfileId] = useState<string | null>(null);
	const [hasSession, setHasSession] = useState(false);
	const branding = useBranding();
	const initials = brandInitials(branding);

	useEffect(() => {
		setSavedProfileId(getStoredProfileId());
		setHasSession(hasStoredSessionHint());
	}, []);

	const hasContinuation = Boolean(savedProfileId || hasSession);
	const studentHref = savedProfileId ? "/dashboard" : "/login";

	return (
		<main className="bg-white">
			<section className="mx-auto grid max-w-6xl gap-4 px-5 pt-4 pb-6 sm:px-6 sm:pt-7 sm:pb-8 lg:grid-cols-[0.86fr_1.14fr] lg:items-stretch lg:pt-10">
				<GlassPanel className="flex flex-col justify-between gap-4 p-4 sm:gap-6 sm:p-7">
					<div>
						<div className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-950 text-sm font-bold text-white sm:h-11 sm:w-11">
							{initials}
						</div>
						<h1 className="mt-4 text-3xl font-semibold tracking-tight text-zinc-950 sm:mt-5 sm:text-5xl">
							{branding.homepage.headline || branding.product_name}
						</h1>
						<p className="mt-3 max-w-xl text-sm leading-6 text-zinc-600 sm:mt-4 sm:text-base sm:leading-7">
							{branding.homepage.description ||
								"Choose the right academic path, build placement readiness, and keep every recommendation connected to the student's goals, strengths, and next action."}
						</p>
					</div>
					<div className="hidden gap-3 border-t border-black/10 pt-5 sm:grid">
						<div className="grid gap-2 sm:grid-cols-3">
							<StatusBadge tone="orange">Branch guidance</StatusBadge>
							<StatusBadge tone="dark">Placement readiness</StatusBadge>
							<StatusBadge tone="neutral">Admin visibility</StatusBadge>
						</div>
						<div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
							<div>
								<p className="text-sm font-semibold text-zinc-950">
									{hasContinuation
										? "Resume your saved workspace"
										: "Already have an account?"}
								</p>
								<p className="mt-1 text-sm leading-5 text-zinc-600">
									{hasContinuation
										? "Continue with your active student or admin workspace."
										: "Log in to continue an existing student or admin workspace."}
								</p>
							</div>
							<Link
								href={hasContinuation ? studentHref : "/login"}
								className={buttonClass({
									variant: hasContinuation ? "primary" : "secondary",
									className: "w-fit shrink-0",
								})}
							>
								{hasContinuation ? "Continue" : "Log in"}
							</Link>
						</div>
					</div>
				</GlassPanel>

				<section className="grid gap-4 lg:grid-cols-3">
					<GatewayPath
						title={
							branding.branch_guidance.title ||
							"Find my best-fit SAGE/SIRT program"
						}
						description={
							branding.branch_guidance.description ||
							"For 12th students choosing a branch with subject strengths, interests, confidence, and expectations."
						}
						href="/signup?type=twelfth_student"
						action="Start branch guidance"
						icon={GraduationCap}
						meta="12th"
					/>
					<GatewayPath
						title={
							branding.placement_readiness.title ||
							"Build my placement readiness plan"
						}
						description={
							branding.placement_readiness.description ||
							"For college students connecting skills, projects, resume, training, internships, and career goals."
						}
						href="/signup?type=college_student"
						action="Start placement plan"
						icon={BriefcaseBusiness}
						emphasis="dark"
						meta="College"
					/>
					<GatewayPath
						title={branding.admin_command.title || "Open the command center"}
						description={
							branding.admin_command.description ||
							"For administrators reviewing readiness, student risk, knowledge quality, and priority actions."
						}
						href="/login"
						action="Admin login"
						icon={ShieldCheck}
						emphasis="dark"
						meta="Admin"
					/>
					<div className="flex items-center justify-between gap-3 rounded-xl border border-black/10 bg-white/80 p-3 shadow-[0_8px_22px_rgba(15,23,42,0.04)] sm:hidden">
						<div className="min-w-0">
							<p className="text-sm font-semibold text-zinc-950">
								{hasContinuation
									? "Resume your saved workspace"
									: "Already have an account?"}
							</p>
							<p className="mt-0.5 text-xs leading-5 text-zinc-600">
								{hasContinuation
									? "Continue from your active workspace."
									: "Log in to continue an existing workspace."}
							</p>
						</div>
						<Link
							href={hasContinuation ? studentHref : "/login"}
							className={buttonClass({
								variant: hasContinuation ? "primary" : "secondary",
								className: "min-h-9 shrink-0 px-3 py-1.5 text-xs",
							})}
						>
							{hasContinuation ? "Continue" : "Log in"}
						</Link>
					</div>
				</section>
			</section>

			<section className="border-y border-black/10 bg-zinc-50">
				<div className="mx-auto max-w-6xl px-5 py-8 sm:px-6">
					<div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
						<div>
							<h2 className="text-2xl font-semibold tracking-tight text-zinc-950">
								Real capabilities in one readiness loop
							</h2>
							<p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
								{branding.homepage.feature_intro ||
									"SAGE combines student intake, AI analysis, personalized copilot support, and practical readiness tools in the same workflow."}
							</p>
						</div>
						<Link
							href="/signup"
							className={buttonClass({
								variant: "secondary",
								className: "w-fit",
							})}
						>
							Create workspace
						</Link>
					</div>
					<div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
						{features.map((feature) => (
							<FeatureCard key={feature.title} {...feature} />
						))}
					</div>
				</div>
			</section>

			<section className="mx-auto max-w-6xl space-y-4 px-5 py-8 sm:px-6">
				<div className="flex items-center gap-3">
					<div className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500 text-white">
						<Route className="h-5 w-5" />
					</div>
					<div>
						<h2 className="text-2xl font-semibold tracking-tight text-zinc-950">
							Two student journeys, one product rhythm
						</h2>
						<p className="mt-1 text-sm leading-6 text-zinc-600">
							Each path starts with a profile and ends with actions a student or
							institution can review.
						</p>
					</div>
				</div>
				<WorkflowBand
					title="12th student branch guidance"
					description={
						branding.branch_guidance.workflow ||
						"Turn subjects, interests, confidence, and expectations into SAGE/SIRT program guidance."
					}
					steps={branchSteps}
				/>
				<WorkflowBand
					title="College placement readiness"
					description="Turn academic record, skills, projects, resume, and career goals into placement actions."
					steps={placementSteps}
					tone="dark"
				/>
			</section>

			<section className="mx-auto max-w-6xl px-5 pb-10 sm:px-6">
				<GlassPanel className="grid gap-6 p-6 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
					<div>
						<div className="flex h-11 w-11 items-center justify-center rounded-xl bg-zinc-950 text-white">
							<Sparkles className="h-5 w-5" />
						</div>
						<h2 className="mt-4 text-2xl font-semibold tracking-tight text-zinc-950">
							Personalized multi-agent copilot
						</h2>
						<p className="mt-2 text-sm leading-6 text-zinc-600">
							{branding.product_name} coordinates profile understanding, quiz
							signals, career reasoning, and readiness planning so each student
							gets guidance that feels specific to their stage.
						</p>
					</div>
					<div className="grid gap-3 sm:grid-cols-3">
						<TrustItem
							title="Profile-aware guidance"
							description="The copilot adapts advice to student type, interests, academic context, and goals."
							icon={UserRoundCheck}
						/>
						<TrustItem
							title="Multi-agent reasoning"
							description="Specialized agents focus on branch fit, placement readiness, and recommendation quality."
							icon={Bot}
						/>
						<TrustItem
							title="Action copilot"
							description="Outputs turn into practical next steps across profile, quiz, analysis, resume, training, and internship."
							icon={MessagesSquare}
						/>
					</div>
				</GlassPanel>
			</section>
		</main>
	);
}

function TrustItem({
	title,
	description,
	icon: Icon,
}: {
	title: string;
	description: string;
	icon: ComponentType<{ className?: string }>;
}) {
	return (
		<div className="rounded-xl border border-black/10 bg-zinc-50 p-4">
			<div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-white text-orange-600 shadow-[0_6px_16px_rgba(15,23,42,0.06)]">
				<Icon className="h-4 w-4" />
			</div>
			<h3 className="text-sm font-semibold text-zinc-950">{title}</h3>
			<p className="mt-2 text-sm leading-6 text-zinc-600">{description}</p>
		</div>
	);
}
