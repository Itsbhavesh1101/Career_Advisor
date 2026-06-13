import assert from "node:assert/strict";
import test from "node:test";

import {
	buildApplicationStatusSummary,
	buildOpportunityReviewSummary,
	buildPlacementActivityLabel,
	buildUpcomingActionSummary,
	groupApplicationsByStatus,
} from "./placementAdminUi.ts";

const applications = [
	{
		id: 1,
		opportunity_id: 10,
		status: "interested",
		admin_notes: null,
		created_at: "2026-05-25T00:00:00Z",
	},
	{
		id: 2,
		opportunity_id: 10,
		status: "applied",
		admin_notes: "Resume received.",
		created_at: "2026-05-24T00:00:00Z",
	},
	{
		id: 3,
		opportunity_id: 11,
		status: "interview_scheduled",
		admin_notes: null,
		created_at: "2026-05-23T00:00:00Z",
	},
	{
		id: 5,
		opportunity_id: 10,
		status: "offer_made",
		admin_notes: "Offer pending acknowledgement.",
		created_at: "2026-05-21T00:00:00Z",
	},
	{
		id: 4,
		opportunity_id: 12,
		status: "withdrawn",
		admin_notes: null,
		created_at: "2026-05-22T00:00:00Z",
	},
] as const;

test("summarizes applications into operational counts", () => {
	const summary = buildApplicationStatusSummary(applications);

	assert.equal(summary.total, 5);
	assert.equal(summary.needsReview, 1);
	assert.equal(summary.activePipeline, 4);
	assert.equal(summary.byStatus.interested, 1);
	assert.equal(summary.byStatus.applied, 1);
	assert.equal(summary.byStatus.interview_scheduled, 1);
	assert.equal(summary.byStatus.offer_made, 1);
	assert.equal(summary.byStatus.withdrawn, 1);
});

test("groups applications in review order and omits empty groups by default", () => {
	const groups = groupApplicationsByStatus(applications);

	assert.deepEqual(
		groups.map((group) => [group.status, group.label, group.items.length]),
		[
			["interested", "Interested", 1],
			["applied", "Applied", 1],
			["interview_scheduled", "Interview scheduled", 1],
			["offer_made", "Offer made", 1],
			["withdrawn", "Withdrawn", 1],
		],
	);
});

test("builds selected opportunity review summary", () => {
	const summary = buildOpportunityReviewSummary(
		{
			id: 10,
			title: "Backend Drive",
			company: "Campus Recruiter",
			opportunity_type: "placement",
			status: "active",
			deadline_at: "2026-06-10T00:00:00Z",
			required_skills: ["Python", "SQL"],
			applicant_count: 5,
			package_label: "6-8 LPA",
			vacancies: 4,
			contact_name: "TnP Officer",
			contact_email: "tnp@example.com",
			hiring_stages: ["Resume", "Technical", "HR"],
		},
		applications,
	);

	assert.deepEqual(summary, {
		title: "Backend Drive",
		company: "Campus Recruiter",
		status: "active",
		type: "placement",
		deadlineLabel: "10 Jun 2026",
		requiredSkillsLabel: "Python, SQL",
		packageLabel: "6-8 LPA",
		vacanciesLabel: "4 openings",
		contactLabel: "TnP Officer, tnp@example.com",
		hiringStagesLabel: "Resume -> Technical -> HR",
		applicantCount: 3,
		needsReview: 1,
	});
});

test("builds compact placement activity labels", () => {
	assert.deepEqual(
		buildPlacementActivityLabel({
			event_type: "application_offer_updated",
			title: "Offer offered",
			opportunity_title: "Backend Drive",
			opportunity_company: "Campus Recruiter",
			student_name: "Student One",
			created_at: "2026-05-25T10:30:00Z",
		}),
		{
			title: "Offer offered",
			context: "Student One - Backend Drive - Campus Recruiter",
			when: "25 May, 10:30",
		},
	);
});

test("summarizes upcoming placement actions by due urgency", () => {
	const summary = buildUpcomingActionSummary([
		{
			action_type: "application_next_step",
			due_at: "2026-06-01T09:00:00Z",
			status: "screening",
		},
		{
			action_type: "interview_round",
			due_at: "2026-06-02T09:00:00Z",
			status: "scheduled",
		},
		{
			action_type: "offer_joining",
			due_at: "2026-07-01T09:00:00Z",
			status: "offered",
		},
	]);

	assert.deepEqual(summary, {
		total: 3,
		nextActionLabel: "Next action: 01 Jun, 09:00",
		byType: {
			application_next_step: 1,
			interview_round: 1,
			offer_joining: 1,
			opportunity_deadline: 0,
		},
	});
});
