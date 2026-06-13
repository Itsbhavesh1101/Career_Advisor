import assert from "node:assert/strict";
import test from "node:test";

import {
	buildManagedItemDetailSummary,
	getManagedItemTypeConfig,
	getPayloadTemplate,
} from "./adminManagementUi.ts";

test("provides configs for institution content management categories", () => {
	assert.equal(
		getManagedItemTypeConfig("institution_policy").label,
		"Policies",
	);
	assert.equal(
		getManagedItemTypeConfig("knowledge_template").label,
		"Knowledge templates",
	);
	assert.equal(
		getManagedItemTypeConfig("institution_content").label,
		"Institution content",
	);
});

test("builds safe payload templates for non-technical admins", () => {
	assert.deepEqual(getPayloadTemplate("institution_policy"), {
		policy_area: "placement",
		applies_to: ["college_student"],
		rules: ["Add the policy rule students or counselors should follow."],
		owner: "Placement Cell",
	});
	assert.deepEqual(getPayloadTemplate("knowledge_template"), {
		source_type: "faq",
		required_sections: ["overview", "eligibility", "student action"],
		review_cadence_days: 90,
		owner: "Knowledge Owner",
	});
});

test("summarizes managed item details without exposing raw JSON first", () => {
	assert.equal(
		buildManagedItemDetailSummary({
			item_type: "internship_opportunity",
			payload: {
				company: "Innovation Lab",
				duration: "8 weeks",
				skills: ["Python", "ML"],
			},
		}),
		"Innovation Lab - 8 weeks - Python, ML",
	);
	assert.equal(
		buildManagedItemDetailSummary({
			item_type: "institution_content",
			payload: {
				content_area: "homepage",
				audience: "all",
				headline: "Personalized multi-agent guidance",
			},
		}),
		"homepage - all - Personalized multi-agent guidance",
	);
});
