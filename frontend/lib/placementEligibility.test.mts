import assert from "node:assert/strict";
import test from "node:test";
import {
	buildEligibilityFromControls,
	hasAdvancedEligibilityKeys,
	parseAdvancedEligibilityJson,
	parseEligibilityToControls,
} from "./placementEligibility.ts";

test("builds college eligibility from guided controls", () => {
	assert.deepEqual(
		buildEligibilityFromControls({
			studentTypeScope: "college",
			minCgpa: "7.5",
			specializations: "CSE, AI & ML, CSE",
		}),
		{
			student_types: ["college_student"],
			min_cgpa: 7.5,
			specializations: ["CSE", "AI & ML"],
		},
	);
});

test("omits college-only filters for twelfth-only opportunities", () => {
	assert.deepEqual(
		buildEligibilityFromControls({
			studentTypeScope: "twelfth",
			minCgpa: "8",
			specializations: "CSE",
		}),
		{
			student_types: ["twelfth_student"],
		},
	);
});

test("parses known eligibility JSON back into guided controls", () => {
	assert.deepEqual(
		parseEligibilityToControls({
			student_types: ["twelfth_student", "college_student"],
			min_cgpa: 6.5,
			specializations: ["CSE", "Data Science"],
		}),
		{
			studentTypeScope: "both",
			minCgpa: "6.5",
			specializations: "CSE, Data Science",
		},
	);
});

test("detects advanced eligibility keys and validates JSON override", () => {
	assert.equal(
		hasAdvancedEligibilityKeys({
			student_types: ["college_student"],
			graduation_years: [2026, 2027],
		}),
		true,
	);
	assert.deepEqual(
		parseAdvancedEligibilityJson('{"student_types":["college_student"]}'),
		{
			student_types: ["college_student"],
		},
	);
	assert.throws(
		() => parseAdvancedEligibilityJson("[1,2,3]"),
		/Eligibility must be a JSON object/,
	);
});
