"use client";

import type { ReactNode } from "react";

export function cn(...classes: Array<string | false | null | undefined>) {
	return classes.filter(Boolean).join(" ");
}

type GlassPanelProps = {
	children: ReactNode;
	className?: string;
	tone?: "light" | "dark" | "orange" | "danger" | "success" | "warning";
	as?: "section" | "div" | "article";
};

const panelTones: Record<NonNullable<GlassPanelProps["tone"]>, string> = {
	light:
		"border-black/10 bg-white text-zinc-950 shadow-[0_8px_26px_rgba(15,23,42,0.05)]",
	dark: "border-zinc-900 bg-zinc-950 text-white shadow-[0_12px_30px_rgba(0,0,0,0.16)]",
	orange:
		"border-orange-200 bg-orange-50 text-zinc-950 shadow-[0_8px_26px_rgba(234,88,12,0.08)]",
	danger:
		"border-red-200 bg-red-50 text-red-950 shadow-[0_8px_26px_rgba(185,28,28,0.06)]",
	success:
		"border-emerald-200 bg-emerald-50 text-emerald-950 shadow-[0_8px_26px_rgba(5,150,105,0.06)]",
	warning:
		"border-amber-200 bg-amber-50 text-amber-950 shadow-[0_8px_26px_rgba(217,119,6,0.06)]",
};

export function GlassPanel({
	children,
	className,
	tone = "light",
	as = "section",
}: GlassPanelProps) {
	const Component = as;
	return (
		<Component
			className={cn("rounded-xl border p-5", panelTones[tone], className)}
		>
			{children}
		</Component>
	);
}

export function PageShell({
	children,
	className,
}: {
	children: ReactNode;
	className?: string;
}) {
	return (
		<main
			className={cn(
				"mx-auto max-w-6xl space-y-5 px-5 py-6 sm:px-6 lg:py-8",
				className,
			)}
		>
			{children}
		</main>
	);
}

export function PublicWorkShell({
	title,
	description,
	children,
	aside,
	className,
}: {
	title: string;
	description: string;
	children: ReactNode;
	aside?: ReactNode;
	className?: string;
}) {
	return (
		<main
			className={cn(
				"mx-auto grid min-h-[calc(100svh-4.1rem)] max-w-6xl gap-5 px-5 py-6 sm:px-6 lg:grid-cols-[0.88fr_1fr] lg:items-center lg:py-8",
				className,
			)}
		>
			<GlassPanel className="space-y-5 p-5 sm:p-6">
				<div>
					<h1 className="text-3xl font-semibold tracking-tight text-zinc-950 sm:text-4xl">
						{title}
					</h1>
					<p className="mt-3 text-sm leading-6 text-zinc-600">{description}</p>
				</div>
				{aside ? (
					<div className="border-t border-black/10 pt-4">{aside}</div>
				) : null}
			</GlassPanel>
			{children}
		</main>
	);
}

type PageHeaderProps = {
	title: string;
	description?: string;
	actions?: ReactNode;
	className?: string;
};

export function PageHeader({
	title,
	description,
	actions,
	className,
}: PageHeaderProps) {
	return (
		<header
			className={cn(
				"flex flex-col gap-4 border-b border-black/10 pb-5 md:flex-row md:items-end md:justify-between",
				className,
			)}
		>
			<div className="max-w-3xl">
				<h1 className="text-3xl font-semibold tracking-tight text-zinc-950 md:text-4xl">
					{title}
				</h1>
				{description ? (
					<p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
						{description}
					</p>
				) : null}
			</div>
			{actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
		</header>
	);
}

type ButtonLinkProps = {
	children?: ReactNode;
	className?: string;
	variant?: "primary" | "secondary" | "ghost" | "dark";
};

const buttonVariants: Record<
	NonNullable<ButtonLinkProps["variant"]>,
	string
> = {
	primary: "bg-orange-500 text-white shadow-sm hover:bg-orange-600",
	secondary:
		"border border-black/10 bg-white text-zinc-950 shadow-sm hover:border-orange-300 hover:bg-orange-50",
	ghost:
		"border border-transparent text-zinc-700 hover:border-black/10 hover:bg-white/70",
	dark: "bg-zinc-950 text-white hover:bg-zinc-800",
};

export function buttonClass({
	className,
	variant = "primary",
}: ButtonLinkProps = {}) {
	return cn(
		"inline-flex min-h-10 items-center justify-center rounded-full px-4 py-2 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-orange-300 disabled:cursor-not-allowed disabled:opacity-60",
		buttonVariants[variant],
		className,
	);
}

type ActionCardProps = {
	title: string;
	description: string;
	children?: ReactNode;
	className?: string;
	accent?: "orange" | "black";
};

export function ActionCard({
	title,
	description,
	children,
	className,
	accent = "orange",
}: ActionCardProps) {
	const accentClass =
		accent === "black" ? "bg-zinc-950 text-white" : "bg-orange-500 text-white";
	return (
		<GlassPanel
			className={cn(
				"group flex min-h-[13rem] flex-col justify-between gap-6 transition hover:-translate-y-0.5 hover:border-orange-300/70",
				className,
			)}
		>
			<div>
				<span className={cn("inline-flex h-9 w-9 rounded-full", accentClass)} />
				<h2 className="mt-5 text-xl font-semibold text-zinc-950">{title}</h2>
				<p className="mt-2 text-sm leading-6 text-zinc-600">{description}</p>
			</div>
			{children}
		</GlassPanel>
	);
}

type StatusBadgeProps = {
	children: ReactNode;
	tone?: "neutral" | "orange" | "success" | "warning" | "danger" | "dark";
	className?: string;
};

const badgeTones: Record<NonNullable<StatusBadgeProps["tone"]>, string> = {
	neutral: "border-black/10 bg-white/70 text-zinc-700",
	orange: "border-orange-200 bg-orange-50 text-orange-800",
	success: "border-emerald-200 bg-emerald-50 text-emerald-800",
	warning: "border-amber-200 bg-amber-50 text-amber-800",
	danger: "border-red-200 bg-red-50 text-red-800",
	dark: "border-zinc-900 bg-zinc-950 text-white",
};

export function StatusBadge({
	children,
	tone = "neutral",
	className,
}: StatusBadgeProps) {
	return (
		<span
			className={cn(
				"inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold",
				badgeTones[tone],
				className,
			)}
		>
			{children}
		</span>
	);
}

export function Tag({
	children,
	tone = "neutral",
	className,
}: StatusBadgeProps) {
	return (
		<span
			className={cn(
				"inline-flex max-w-full items-center rounded-full border px-2.5 py-1 text-xs font-medium",
				badgeTones[tone],
				className,
			)}
		>
			{children}
		</span>
	);
}

type MetricTileProps = {
	label: string;
	value: ReactNode;
	helper?: string;
	tone?: StatusBadgeProps["tone"];
	statusLabel?: string;
};

const metricStatusLabels: Partial<
	Record<NonNullable<StatusBadgeProps["tone"]>, string>
> = {
	neutral: "Live",
	orange: "Priority",
	success: "Clear",
	warning: "Review",
	danger: "Act now",
	dark: "Active",
};

export function MetricTile({
	label,
	value,
	helper,
	tone = "neutral",
	statusLabel,
}: MetricTileProps) {
	return (
		<div className="rounded-lg border border-black/10 bg-white p-4 shadow-[0_6px_18px_rgba(15,23,42,0.04)]">
			<div className="flex items-start justify-between gap-3">
				<p className="text-sm font-medium text-zinc-600">{label}</p>
				<StatusBadge tone={tone}>
					{statusLabel ?? metricStatusLabels[tone] ?? "Live"}
				</StatusBadge>
			</div>
			<p className="mt-3 text-3xl font-semibold tracking-tight text-zinc-950">
				{value}
			</p>
			{helper ? <p className="mt-1 text-xs text-zinc-500">{helper}</p> : null}
		</div>
	);
}

export function EmptyState({
	title,
	description,
	action,
}: {
	title: string;
	description?: string;
	action?: ReactNode;
}) {
	return (
		<GlassPanel className="text-center">
			<p className="text-base font-semibold text-zinc-950">{title}</p>
			{description ? (
				<p className="mx-auto mt-2 max-w-md text-sm leading-6 text-zinc-600">
					{description}
				</p>
			) : null}
			{action ? <div className="mt-4 flex justify-center">{action}</div> : null}
		</GlassPanel>
	);
}

export function Notice({
	title,
	description,
	tone = "orange",
	action,
}: {
	title: string;
	description?: string;
	tone?: "orange" | "success" | "warning" | "danger" | "neutral";
	action?: ReactNode;
}) {
	const noticeTone =
		tone === "success"
			? "border-emerald-200 bg-emerald-50 text-emerald-950"
			: tone === "warning"
				? "border-amber-200 bg-amber-50 text-amber-950"
				: tone === "danger"
					? "border-red-200 bg-red-50 text-red-950"
					: tone === "neutral"
						? "border-black/10 bg-white/70 text-zinc-950"
						: "border-orange-200 bg-orange-50 text-orange-950";
	return (
		<div className={cn("rounded-xl border p-4", noticeTone)}>
			<div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
				<div>
					<p className="font-semibold">{title}</p>
					{description ? (
						<p className="mt-1 text-sm leading-6 opacity-75">{description}</p>
					) : null}
				</div>
				{action ? <div className="shrink-0">{action}</div> : null}
			</div>
		</div>
	);
}

export function SectionTabs<T extends string>({
	items,
	active,
	onChange,
}: {
	items: Array<{ id: T; label: string; count?: number }>;
	active: T;
	onChange: (id: T) => void;
}) {
	return (
		<div className="flex gap-1 overflow-x-auto rounded-full border border-black/10 bg-white p-1 shadow-sm">
			{items.map((item) => (
				<button
					key={item.id}
					type="button"
					onClick={() => onChange(item.id)}
					className={cn(
						"whitespace-nowrap rounded-full px-4 py-2 text-sm font-semibold transition",
						active === item.id
							? "bg-zinc-950 text-white shadow-sm"
							: "text-zinc-600 hover:bg-orange-50 hover:text-zinc-950",
					)}
				>
					{item.label}
					{typeof item.count === "number" ? (
						<span className="ml-2 opacity-70">{item.count}</span>
					) : null}
				</button>
			))}
		</div>
	);
}

export function DataTable({
	children,
	className,
}: {
	children: ReactNode;
	className?: string;
}) {
	return (
		<div
			className={cn(
				"overflow-x-auto rounded-xl border border-black/10 bg-white shadow-sm",
				className,
			)}
		>
			<table className="w-full text-left text-sm text-zinc-700">
				{children}
			</table>
		</div>
	);
}

export const fieldControlClass =
	"w-full rounded-lg border border-black/10 bg-white px-3 py-2 text-sm text-zinc-950 outline-none transition placeholder:text-zinc-400 focus:border-orange-300 focus:ring-2 focus:ring-orange-200 disabled:cursor-not-allowed disabled:bg-zinc-100 disabled:text-zinc-500";

export function Field({
	label,
	children,
	helper,
	htmlFor,
}: {
	label: string;
	children: ReactNode;
	helper?: string;
	htmlFor?: string;
}) {
	const labelContent = htmlFor ? (
		<label htmlFor={htmlFor} className="block">
			{label}
		</label>
	) : (
		<span>{label}</span>
	);

	return (
		<div className="block space-y-2 text-sm font-semibold text-zinc-700">
			{labelContent}
			{children}
			{helper ? (
				<span className="block text-xs font-normal leading-5 text-zinc-500">
					{helper}
				</span>
			) : null}
		</div>
	);
}

export function FormSection({
	title,
	description,
	children,
}: {
	title: string;
	description?: string;
	children: ReactNode;
}) {
	return (
		<section className="space-y-4 rounded-xl border border-black/10 bg-zinc-50/70 p-4">
			<div>
				<h2 className="text-sm font-semibold text-zinc-950">{title}</h2>
				{description ? (
					<p className="mt-1 text-xs leading-5 text-zinc-500">{description}</p>
				) : null}
			</div>
			{children}
		</section>
	);
}

export function ScoreBar({
	value,
	tone = "orange",
	label,
}: {
	value: number;
	tone?: "orange" | "success" | "warning" | "danger" | "dark";
	label?: string;
}) {
	const safeValue = Math.max(
		0,
		Math.min(100, Number.isFinite(value) ? value : 0),
	);
	const fill =
		tone === "success"
			? "bg-emerald-500"
			: tone === "warning"
				? "bg-amber-500"
				: tone === "danger"
					? "bg-red-500"
					: tone === "dark"
						? "bg-zinc-950"
						: "bg-orange-500";
	return (
		<div>
			{label ? (
				<div className="mb-1 flex items-center justify-between text-xs text-zinc-500">
					<span>{label}</span>
					<span className="font-semibold text-zinc-800">{safeValue}%</span>
				</div>
			) : null}
			<div className="h-2 overflow-hidden rounded-full bg-zinc-200">
				<div
					className={cn("h-full rounded-full transition-all", fill)}
					style={{ width: `${safeValue}%` }}
				/>
			</div>
		</div>
	);
}

export function CompactActionList({
	items,
	emptyText = "No actions yet.",
	limit = 4,
}: {
	items: string[];
	emptyText?: string;
	limit?: number;
}) {
	const safeItems = items
		.map((item) => item.trim())
		.filter(Boolean)
		.slice(0, limit);
	if (!safeItems.length) {
		return <p className="text-sm text-zinc-500">{emptyText}</p>;
	}
	return (
		<ul className="space-y-2 text-sm text-zinc-700">
			{safeItems.map((item) => (
				<li key={item} className="flex gap-2">
					<span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-orange-500" />
					<span className="break-words">{item}</span>
				</li>
			))}
		</ul>
	);
}

export function Toolbar({
	children,
	className,
}: {
	children: ReactNode;
	className?: string;
}) {
	return (
		<div
			className={cn(
				"flex flex-wrap items-center gap-3 rounded-xl border border-black/10 bg-white p-3 shadow-sm",
				className,
			)}
		>
			{children}
		</div>
	);
}

export function EvidenceDrawer({
	title,
	children,
	defaultOpen = false,
}: {
	title: string;
	children: ReactNode;
	defaultOpen?: boolean;
}) {
	return (
		<details
			open={defaultOpen}
			className="rounded-xl border border-black/10 bg-white/60 p-4"
		>
			<summary className="cursor-pointer text-sm font-semibold text-zinc-950">
				{title}
			</summary>
			<div className="mt-3 text-sm leading-6 text-zinc-600">{children}</div>
		</details>
	);
}
