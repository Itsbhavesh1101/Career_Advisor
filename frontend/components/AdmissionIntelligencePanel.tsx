"use client";

import { RefreshCw } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
	buttonClass,
	CompactActionList,
	DataTable,
	EmptyState,
	GlassPanel,
	MetricTile,
	Notice,
	ScoreBar,
	StatusBadge,
	Tag,
} from "@/components/ui";
import {
	type AdmissionDashboardRead,
	type AdmissionLeadRead,
	getAdmissionIntelligenceDashboard,
} from "@/lib/api";

function titleize(value: string): string {
	return value
		.replace(/[_-]+/g, " ")
		.replace(/\s+/g, " ")
		.trim()
		.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function confidenceValue(confidence: number | null): number {
	return typeof confidence === "number"
		? Math.max(0, Math.min(100, confidence))
		: 0;
}

function priorityTone(
	priority: string,
): "danger" | "warning" | "orange" | "success" {
	switch (priority.toLowerCase()) {
		case "urgent":
			return "danger";
		case "high":
			return "warning";
		case "medium":
			return "orange";
		default:
			return "success";
	}
}

function LeadRow({ lead }: { lead: AdmissionLeadRead }) {
	const brief = lead.counselor_brief;
	const confidence = confidenceValue(lead.confidence);
	const signals = lead.lost_reason_signals
		.map((signal) => signal.trim())
		.filter(Boolean)
		.slice(0, 3);

	return (
		<tr className="border-b border-black/5 align-top last:border-0">
			<td className="px-4 py-4">
				<p className="font-semibold text-zinc-950">{lead.student_name}</p>
				<p className="mt-1 text-xs text-zinc-500">
					{lead.current_interest || "Interest pending"} /{" "}
					{lead.preferred_stream || "Stream pending"}
				</p>
				<div className="mt-2 flex flex-wrap gap-1.5">
					{signals.length ? (
						signals.map((signal) => <Tag key={signal}>{signal}</Tag>)
					) : (
						<Tag>no loss signal</Tag>
					)}
				</div>
			</td>
			<td className="px-4 py-4">
				<p className="font-semibold text-zinc-950">
					{lead.recommended_program || "Program fit pending"}
				</p>
				<div className="mt-2 max-w-56">
					<ScoreBar value={confidence} label="confidence" />
				</div>
			</td>
			<td className="px-4 py-4">
				<div className="flex flex-wrap gap-2">
					<StatusBadge tone={priorityTone(lead.priority)}>
						{titleize(lead.priority)}
					</StatusBadge>
					<Tag>{titleize(lead.status)}</Tag>
				</div>
			</td>
			<td className="px-4 py-4">
				<CompactActionList
					items={[
						...brief.talking_points.slice(0, 2),
						...brief.follow_up_questions.slice(0, 1),
					]}
					emptyText="No counselor notes yet."
					limit={3}
				/>
			</td>
			<td className="px-4 py-4">
				<Link
					href={`/analysis/${lead.profile_id}`}
					className={buttonClass({
						variant: "ghost",
						className: "min-h-8 px-3 py-1 text-xs",
					})}
				>
					Open
				</Link>
			</td>
		</tr>
	);
}

export default function AdmissionIntelligencePanel() {
	const [dashboard, setDashboard] = useState<AdmissionDashboardRead | null>(
		null,
	);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	const loadDashboard = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const data = await getAdmissionIntelligenceDashboard(12);
			setDashboard(data);
		} catch (err) {
			setDashboard(null);
			setError(
				err instanceof Error
					? err.message
					: "Failed to load admission intelligence.",
			);
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		void loadDashboard();
	}, [loadDashboard]);

	const sortedLeads = useMemo(
		() =>
			[...(dashboard?.leads ?? [])].sort(
				(a, b) =>
					priorityRank(a.priority) - priorityRank(b.priority) ||
					confidenceValue(b.confidence) - confidenceValue(a.confidence),
			),
		[dashboard],
	);

	const metrics = dashboard?.metrics;

	return (
		<div className="space-y-5">
			<div className="flex flex-wrap items-start justify-between gap-3">
				<div>
					<h2 className="text-2xl font-semibold text-zinc-950">Admissions</h2>
					<p className="mt-1 text-sm leading-6 text-zinc-600">
						Prioritize 12th-student counseling by intent, program fit, and
						wrong-branch risk.
					</p>
				</div>
				<button
					type="button"
					onClick={() => void loadDashboard()}
					disabled={loading}
					className={buttonClass({ variant: "secondary" })}
				>
					<RefreshCw
						className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`}
					/>
					Refresh
				</button>
			</div>

			{error ? (
				<Notice
					title="Admissions could not load"
					description={error}
					tone="danger"
				/>
			) : null}

			<div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
				<MetricTile
					label="12th profiles"
					value={metrics?.total_twelfth_profiles ?? 0}
					helper={`${metrics?.analyzed_profiles ?? 0} analyzed`}
					tone="orange"
				/>
				<MetricTile
					label="Needs analysis"
					value={metrics?.needs_analysis ?? 0}
					helper="No fit snapshot"
					tone={(metrics?.needs_analysis ?? 0) > 0 ? "warning" : "success"}
				/>
				<MetricTile
					label="High intent"
					value={metrics?.high_intent ?? 0}
					helper="Likely counseling"
					tone="success"
				/>
				<MetricTile
					label="Wrong branch"
					value={metrics?.wrong_branch_risk ?? 0}
					helper="Needs expectation check"
					tone={(metrics?.wrong_branch_risk ?? 0) > 0 ? "danger" : "success"}
				/>
				<MetricTile
					label="Counseling ready"
					value={metrics?.ready_for_counseling ?? 0}
					helper="Actionable leads"
					tone="success"
				/>
				<GlassPanel as="div" className="p-4">
					<p className="text-sm font-medium text-zinc-600">Queue rule</p>
					<p className="mt-3 text-sm leading-6 text-zinc-800">
						Urgent risk, high intent, then highest confidence.
					</p>
				</GlassPanel>
			</div>

			{loading ? (
				<GlassPanel>
					<p className="text-sm text-zinc-600">Loading admission queue...</p>
				</GlassPanel>
			) : null}

			{!loading && sortedLeads.length === 0 ? (
				<EmptyState
					title="No admission leads yet"
					description="Create 12th-student profiles and run program guidance to populate this queue."
				/>
			) : (
				<DataTable>
					<thead className="border-b border-black/10 text-xs font-semibold text-zinc-500">
						<tr>
							<th className="px-4 py-3">Student</th>
							<th className="px-4 py-3">Best fit</th>
							<th className="px-4 py-3">Priority</th>
							<th className="px-4 py-3">Counselor action</th>
							<th className="px-4 py-3">Profile</th>
						</tr>
					</thead>
					<tbody>
						{sortedLeads.map((lead) => (
							<LeadRow key={lead.profile_id} lead={lead} />
						))}
					</tbody>
				</DataTable>
			)}
		</div>
	);
}

function priorityRank(priority: string): number {
	switch (priority.toLowerCase()) {
		case "urgent":
			return 0;
		case "high":
			return 1;
		case "medium":
			return 2;
		default:
			return 3;
	}
}
