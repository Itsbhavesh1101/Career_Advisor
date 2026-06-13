import assert from "node:assert/strict";
import test from "node:test";

import {
	buildApplicationNextStep,
	buildMatchReasons,
	buildOpportunityMeta,
	buildStudentPlacementActionLabel,
	canStudentEditApplicationNote,
	canStudentWithdrawApplication,
	isPlacementApplicationFinal,
} from "./placementOpportunityUi.ts";

test("builds readable match reasons from opportunity signals", () => {
	const reasons = buildMatchReasons({
		match_score: 67,
		matched_skills: ["Python", "SQL"],
		required_skills: ["Python", "SQL", "Docker"],
		deadline_at: "2026-06-15T00:00:00Z",
		work_mode: "Hybrid",
		location: "Bhopal",
	});

	assert.deepEqual(reasons, [
		"67% skill match",
		"Matched skills: Python, SQL",
		"Still build: Docker",
		"Deadline: 15 Jun 2026",
		"Hybrid - Bhopal",
	]);
});

test("builds compact opportunity metadata", () => {
	assert.deepEqual(
		buildOpportunityMeta({
			opportunity_type: "internship",
			package_label: "6 LPA",
			vacancies: 2,
			work_mode: "Remote",
			location: "Bengaluru",
			deadline_at: "2026-06-20T00:00:00Z",
		}),
		[
			"Internship",
			"6 LPA",
			"2 openings",
			"Remote",
			"Bengaluru",
			"Deadline 20 Jun",
		],
	);
});

test("deduplicates repeated opportunity metadata labels", () => {
	assert.deepEqual(
		buildOpportunityMeta({
			opportunity_type: "internship",
			work_mode: "Remote",
			location: "Remote",
		}),
		["Internship", "Remote"],
	);
});

test("maps application statuses to student next steps", () => {
	assert.equal(
		buildApplicationNextStep("interested"),
		"Update your note or apply when your resume is ready.",
	);
	assert.equal(
		buildApplicationNextStep("applied"),
		"Track placement-cell updates and keep your resume evidence current.",
	);
	assert.equal(
		buildApplicationNextStep("shortlisted"),
		"Prepare for the next screening or interview round.",
	);
	assert.equal(
		buildApplicationNextStep("screening"),
		"Your profile is under screening. Keep resume evidence and availability current.",
	);
	assert.equal(
		buildApplicationNextStep("interview_scheduled"),
		"Prepare for the scheduled interview and keep documents ready.",
	);
	assert.equal(
		buildApplicationNextStep("offer_made"),
		"Review the offer, confirm documents, and wait for joining instructions.",
	);
	assert.equal(
		buildApplicationNextStep("joined"),
		"Joining is complete. Keep records updated with the placement cell.",
	);
	assert.equal(
		buildApplicationNextStep("withdrawn"),
		"This application is withdrawn. Use matched opportunities for another fit.",
	);
});

test("keeps student application actions scoped to allowed statuses", () => {
	assert.equal(canStudentEditApplicationNote("interested"), true);
	assert.equal(canStudentEditApplicationNote("applied"), true);
	assert.equal(canStudentEditApplicationNote("screening"), false);
	assert.equal(canStudentEditApplicationNote("interview_scheduled"), false);
	assert.equal(canStudentEditApplicationNote("offer_made"), false);

	assert.equal(canStudentWithdrawApplication("screening"), true);
	assert.equal(canStudentWithdrawApplication("offer_made"), true);
	assert.equal(canStudentWithdrawApplication("placed"), false);
	assert.equal(canStudentWithdrawApplication("joined"), false);
	assert.equal(canStudentWithdrawApplication("not_selected"), false);

	assert.equal(isPlacementApplicationFinal("placed"), true);
	assert.equal(isPlacementApplicationFinal("joined"), true);
	assert.equal(isPlacementApplicationFinal("not_selected"), true);
	assert.equal(isPlacementApplicationFinal("withdrawn"), false);
});

test("builds student placement action labels", () => {
	assert.deepEqual(
		buildStudentPlacementActionLabel({
			action_type: "interview_round",
			title: "Technical interview",
			due_at: "2026-06-03T11:00:00Z",
			opportunity_title: "Backend Drive",
			opportunity_company: "Campus Recruiter",
		}),
		{
			title: "Technical interview",
			context: "Backend Drive - Campus Recruiter",
			when: "03 Jun, 11:00",
		},
	);
});
