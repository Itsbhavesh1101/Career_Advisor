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
	type CompanyReadinessRead,
	type FacultyAdvisorNoteRead,
	getPlacementIntelligenceDashboard,
	type PlacementDashboardRead,
	type PlacementStudentSignalRead,
	type TrainingROISignalRead,
} from "@/lib/api";

function titleize(value: string): string {
	return value
		.replace(/[_-]+/g, " ")
		.replace(/\s+/g, " ")
		.trim()
		.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function percent(value: number | null): string {
	return typeof value === "number" ? `${value}%` : "Pending";
}

function safeScore(value: number | null): number {
	return typeof value === "number" ? Math.max(0, Math.min(100, value)) : 0;
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

function StudentRow({ student }: { student: PlacementStudentSignalRead }) {
	return (
		<tr className="border-b border-black/5 align-top last:border-0">
			<td className="px-4 py-4">
				<p className="font-semibold text-zinc-950">{student.student_name}</p>
				<p className="mt-1 text-xs text-zinc-500">
					{student.program || "Program pending"} / Profile #{student.profile_id}
				</p>
				<div className="mt-2 flex flex-wrap gap-1.5">
					<Tag>{titleize(student.status)}</Tag>
					<StatusBadge tone={priorityTone(student.priority)}>
						{titleize(student.priority)}
					</StatusBadge>
				</div>
			</td>
			<td className="px-4 py-4">
				<div className="min-w-44">
					<ScoreBar
						value={safeScore(student.employability_score)}
						label="employability"
						tone={
							safeScore(student.employability_score) >= 70
								? "success"
								: "warning"
						}
					/>
				</div>
				<p className="mt-2 text-xs text-zinc-500">
					Risk: {student.placement_risk ?? "Pending"}
				</p>
			</td>
			<td className="px-4 py-4">
				<p className="font-semibold text-zinc-950">
					{student.top_company || "Company fit pending"}
				</p>
				<p className="mt-1 text-sm text-zinc-600">
					{percent(student.top_company_score)}
				</p>
			</td>
			<td className="px-4 py-4">
				<CompactActionList
					items={student.recommended_actions}
					emptyText="No action needed."
					limit={3}
				/>
			</td>
			<td className="px-4 py-4">
				<Link
					href={`/analysis/${student.profile_id}`}
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

function CompanyRadar({ companies }: { companies: CompanyReadinessRead[] }) {
	return (
		<GlassPanel className="p-5">
			<h3 className="text-lg font-semibold text-zinc-950">Company readiness</h3>
			<p className="mt-1 text-sm text-zinc-600">
				Where student evidence matches recruiter expectations.
			</p>
			<div className="mt-4 space-y-3">
				{companies.slice(0, 6).map((company) => (
					<div
						key={company.company}
						className="rounded-lg border border-black/10 bg-white/70 p-3"
					>
						<div className="flex items-center justify-between gap-3">
							<p className="font-semibold text-zinc-950">{company.company}</p>
							<span className="text-sm font-semibold text-orange-700">
								{company.average_score}%
							</span>
						</div>
						<ScoreBar value={company.average_score} />
						<div className="mt-2 flex flex-wrap gap-1.5">
							<Tag tone="success">Ready {company.ready_count}</Tag>
							<Tag tone="warning">Watch {company.watch_count}</Tag>
							<Tag tone="danger">Blocked {company.blocked_count}</Tag>
						</div>
					</div>
				))}
				{companies.length === 0 ? (
					<p className="text-sm text-zinc-500">No company-fit records yet.</p>
				) : null}
			</div>
		</GlassPanel>
	);
}

function TrainingROI({ items }: { items: TrainingROISignalRead[] }) {
	return (
		<GlassPanel className="p-5">
			<h3 className="text-lg font-semibold text-zinc-950">Training priority</h3>
			<p className="mt-1 text-sm text-zinc-600">
				Skills that affect the most students.
			</p>
			<div className="mt-4 space-y-3">
				{items.slice(0, 6).map((item) => (
					<div
						key={item.skill}
						className="rounded-lg border border-black/10 bg-white/70 p-3"
					>
						<div className="flex flex-wrap items-center justify-between gap-2">
							<p className="font-semibold text-zinc-950">{item.skill}</p>
							<StatusBadge tone={priorityTone(item.priority)}>
								{titleize(item.priority)}
							</StatusBadge>
						</div>
						<p className="mt-2 text-sm text-zinc-600">
							{item.affected_students} students / +
							{item.expected_readiness_lift}% readiness lift
						</p>
					</div>
				))}
				{items.length === 0 ? (
					<p className="text-sm text-zinc-500">No training ROI signals yet.</p>
				) : null}
			</div>
		</GlassPanel>
	);
}

function AdvisorNotes({ notes }: { notes: FacultyAdvisorNoteRead[] }) {
	return (
		<GlassPanel className="p-5">
			<h3 className="text-lg font-semibold text-zinc-950">Advisor notes</h3>
			<div className="mt-4 space-y-3">
				{notes.slice(0, 4).map((note) => (
					<div
						key={`${note.profile_id}-${note.escalation_level}`}
						className="rounded-lg border border-black/10 bg-white/70 p-3"
					>
						<div className="flex items-center justify-between gap-3">
							<p className="font-semibold text-zinc-950">{note.student_name}</p>
							<StatusBadge tone={priorityTone(note.escalation_level)}>
								{titleize(note.escalation_level)}
							</StatusBadge>
						</div>
						<p className="mt-2 text-sm text-zinc-600">{note.note}</p>
					</div>
				))}
				{notes.length === 0 ? (
					<p className="text-sm text-zinc-500">No advisor escalations yet.</p>
				) : null}
			</div>
		</GlassPanel>
	);
}

export default function PlacementIntelligencePanel() {
	const [dashboard, setDashboard] = useState<PlacementDashboardRead | null>(
		null,
	);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	const loadDashboard = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const data = await getPlacementIntelligenceDashboard(12);
			setDashboard(data);
		} catch (err) {
			setDashboard(null);
			setError(
				err instanceof Error
					? err.message
					: "Failed to load placement intelligence.",
			);
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		void loadDashboard();
	}, [loadDashboard]);

	const sortedStudents = useMemo(
		() =>
			[...(dashboard?.students ?? [])].sort(
				(a, b) =>
					priorityRank(a.priority) - priorityRank(b.priority) ||
					safeScore(a.employability_score) - safeScore(b.employability_score),
			),
		[dashboard],
	);
	const metrics = dashboard?.metrics;

	return (
		<div className="space-y-5">
			<div className="flex flex-wrap items-start justify-between gap-3">
				<div>
					<h2 className="text-2xl font-semibold text-zinc-950">Placements</h2>
					<p className="mt-1 text-sm leading-6 text-zinc-600">
						Find readiness gaps, evidence blockers, company-fit issues, and
						training priorities.
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
					title="Placements could not load"
					description={error}
					tone="danger"
				/>
			) : null}

			<div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
				<MetricTile
					label="College profiles"
					value={metrics?.total_college_profiles ?? 0}
					helper="Placement pool"
					tone="orange"
				/>
				<MetricTile
					label="Placement ready"
					value={metrics?.placement_ready ?? 0}
					helper="Can be shortlisted"
					tone="success"
				/>
				<MetricTile
					label="Needs training"
					value={metrics?.needs_training ?? 0}
					helper="Skill gap queue"
					tone={(metrics?.needs_training ?? 0) > 0 ? "warning" : "success"}
				/>
				<MetricTile
					label="High risk"
					value={metrics?.high_risk ?? 0}
					helper="Advisor escalation"
					tone={(metrics?.high_risk ?? 0) > 0 ? "danger" : "success"}
				/>
				<MetricTile
					label="Company ready"
					value={metrics?.company_ready ?? 0}
					helper="Fit evidence present"
					tone="success"
				/>
				<MetricTile
					label="Average score"
					value={metrics?.average_employability ?? "Pending"}
					helper="Employability"
					tone="orange"
				/>
			</div>

			{loading ? (
				<GlassPanel>
					<p className="text-sm text-zinc-600">Loading placement queue...</p>
				</GlassPanel>
			) : null}

			{!loading && sortedStudents.length === 0 ? (
				<EmptyState
					title="No placement signals yet"
					description="Run college-student analysis, resume review, company fit, and role gaps to populate this queue."
				/>
			) : (
				<DataTable>
					<thead className="border-b border-black/10 text-xs font-semibold text-zinc-500">
						<tr>
							<th className="px-4 py-3">Student</th>
							<th className="px-4 py-3">Readiness</th>
							<th className="px-4 py-3">Company fit</th>
							<th className="px-4 py-3">Next action</th>
							<th className="px-4 py-3">Profile</th>
						</tr>
					</thead>
					<tbody>
						{sortedStudents.map((student) => (
							<StudentRow key={student.profile_id} student={student} />
						))}
					</tbody>
				</DataTable>
			)}

			<section className="grid gap-4 lg:grid-cols-3">
				<CompanyRadar companies={dashboard?.company_radar ?? []} />
				<TrainingROI items={dashboard?.training_roi ?? []} />
				<AdvisorNotes notes={dashboard?.faculty_notes ?? []} />
			</section>
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
