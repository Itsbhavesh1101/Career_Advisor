import type { AdminManagedItemType, JsonValue } from "@/lib/api";

type ManagedItemTypeConfig = {
	value: AdminManagedItemType;
	label: string;
	helper: string;
};

type ManagedItemSummaryInput = {
	item_type: AdminManagedItemType;
	payload?: Record<string, JsonValue>;
};

export const managedItemTypeConfigs: ManagedItemTypeConfig[] = [
	{
		value: "program",
		label: "Programs",
		helper: "Visible in branch/program guidance",
	},
	{
		value: "training_program",
		label: "Training",
		helper: "Feeds training recommendations",
	},
	{
		value: "internship_opportunity",
		label: "Internships",
		helper: "Institution internship catalog",
	},
	{
		value: "placement_company",
		label: "Companies",
		helper: "Placement partner and role targets",
	},
	{
		value: "institution_policy",
		label: "Policies",
		helper: "Rules counselors, students, and placement teams follow",
	},
	{
		value: "knowledge_template",
		label: "Knowledge templates",
		helper: "Reusable structures for trusted knowledge uploads",
	},
	{
		value: "institution_content",
		label: "Institution content",
		helper: "Reusable institution-specific copy and guidance blocks",
	},
];

export function getManagedItemTypeConfig(
	itemType: AdminManagedItemType,
): ManagedItemTypeConfig {
	return (
		managedItemTypeConfigs.find((config) => config.value === itemType) ?? {
			value: itemType,
			label: itemType,
			helper: "Managed content",
		}
	);
}

export function getPayloadTemplate(
	itemType: AdminManagedItemType,
): Record<string, JsonValue> {
	switch (itemType) {
		case "program":
			return {
				school_id: "school-engineering",
				school_name: "School of Engineering",
				campus: "Main Campus",
				degree_level: "undergraduate",
				duration_years: 4,
				priority_skills: ["Python", "Communication"],
				career_paths: ["Software Engineer"],
				admission_fit_signals: ["Strong problem solving"],
				reality_checks: ["Requires regular project practice"],
			};
		case "training_program":
			return {
				focus_skills: ["Communication", "Aptitude"],
				delivery_mode: "workshop",
				duration: "4 weeks",
				owner: "Training Cell",
			};
		case "internship_opportunity":
			return {
				company: "Institution Innovation Lab",
				location: "Campus",
				duration: "8 weeks",
				skills: ["Python", "Communication"],
				eligibility: ["Second year and above"],
				apply_url: "",
				deadline: "",
			};
		case "placement_company":
			return {
				industry: "IT Services",
				target_roles: ["Software Engineer"],
				target_skills: ["Java", "SQL"],
				locations: ["Bhopal", "Remote"],
			};
		case "institution_policy":
			return {
				policy_area: "placement",
				applies_to: ["college_student"],
				rules: ["Add the policy rule students or counselors should follow."],
				owner: "Placement Cell",
			};
		case "knowledge_template":
			return {
				source_type: "faq",
				required_sections: ["overview", "eligibility", "student action"],
				review_cadence_days: 90,
				owner: "Knowledge Owner",
			};
		case "institution_content":
			return {
				content_area: "homepage",
				audience: "all",
				headline: "Personalized multi-agent guidance",
				body: "Add institution-specific guidance copy.",
				cta_label: "",
				cta_url: "",
			};
		default:
			return {};
	}
}

export function buildManagedItemDetailSummary(
	item: ManagedItemSummaryInput,
): string {
	const payload = item.payload ?? {};
	switch (item.item_type) {
		case "program":
			return joinValues([
				valueToText(payload.school_name),
				valueToText(payload.degree_level),
				listToText(payload.priority_skills),
			]);
		case "training_program":
			return joinValues([
				listToText(payload.focus_skills),
				valueToText(payload.delivery_mode),
				valueToText(payload.duration),
			]);
		case "internship_opportunity":
			return joinValues([
				valueToText(payload.company),
				valueToText(payload.duration),
				listToText(payload.skills),
			]);
		case "placement_company":
			return joinValues([
				valueToText(payload.industry),
				listToText(payload.target_roles),
				listToText(payload.target_skills),
			]);
		case "institution_policy":
			return joinValues([
				valueToText(payload.policy_area),
				listToText(payload.applies_to),
				valueToText(payload.owner),
			]);
		case "knowledge_template":
			return joinValues([
				valueToText(payload.source_type),
				listToText(payload.required_sections),
				valueToText(payload.owner),
			]);
		case "institution_content":
			return joinValues([
				valueToText(payload.content_area),
				valueToText(payload.audience),
				valueToText(payload.headline),
			]);
		default:
			return "Managed content";
	}
}

function joinValues(values: Array<string | null>): string {
	return values.filter(Boolean).join(" - ") || "No structured details yet";
}

function listToText(value: JsonValue | undefined): string | null {
	if (!Array.isArray(value)) return null;
	const items = value
		.map((item) => String(item).trim())
		.filter((item) => item.length > 0);
	return items.length ? items.join(", ") : null;
}

function valueToText(value: JsonValue | undefined): string | null {
	if (value === null || value === undefined || Array.isArray(value))
		return null;
	if (typeof value === "object") return null;
	const text = String(value).trim();
	return text || null;
}
