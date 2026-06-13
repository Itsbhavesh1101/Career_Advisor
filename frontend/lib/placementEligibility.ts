import type { JsonValue } from "@/lib/api";

export type EligibilityStudentTypeScope = "college" | "twelfth" | "both";

export interface PlacementEligibilityControls {
	studentTypeScope: EligibilityStudentTypeScope;
	minCgpa: string;
	specializations: string;
}

const knownEligibilityKeys = new Set([
	"student_types",
	"min_cgpa",
	"specializations",
]);

export function buildEligibilityFromControls(
	controls: PlacementEligibilityControls,
): Record<string, JsonValue> {
	const scope = controls.studentTypeScope || "college";
	const eligibility: Record<string, JsonValue> = {
		student_types: studentTypesForScope(scope),
	};

	if (scope !== "twelfth") {
		const minCgpa = parseOptionalCgpa(controls.minCgpa);
		if (minCgpa !== null) {
			eligibility.min_cgpa = minCgpa;
		}

		const specializations = splitUniqueCsv(controls.specializations);
		if (specializations.length) {
			eligibility.specializations = specializations;
		}
	}

	return eligibility;
}

export function parseEligibilityToControls(
	eligibility: Record<string, unknown> | null | undefined,
): PlacementEligibilityControls {
	const studentTypes = stringList(eligibility?.student_types);
	return {
		studentTypeScope: scopeFromStudentTypes(studentTypes),
		minCgpa:
			typeof eligibility?.min_cgpa === "number" ||
			typeof eligibility?.min_cgpa === "string"
				? String(eligibility.min_cgpa)
				: "",
		specializations: stringList(eligibility?.specializations).join(", "),
	};
}

export function parseAdvancedEligibilityJson(
	value: string,
): Record<string, JsonValue> {
	const parsed = JSON.parse(value) as unknown;
	if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
		throw new Error("Eligibility must be a JSON object.");
	}
	return parsed as Record<string, JsonValue>;
}

export function formatEligibilityJson(eligibility: Record<string, JsonValue>) {
	return JSON.stringify(eligibility, null, 2);
}

export function hasAdvancedEligibilityKeys(
	eligibility: Record<string, unknown> | null | undefined,
) {
	return Object.keys(eligibility ?? {}).some(
		(key) => !knownEligibilityKeys.has(key),
	);
}

function studentTypesForScope(scope: EligibilityStudentTypeScope): string[] {
	if (scope === "twelfth") return ["twelfth_student"];
	if (scope === "both") return ["twelfth_student", "college_student"];
	return ["college_student"];
}

function scopeFromStudentTypes(values: string[]): EligibilityStudentTypeScope {
	const normalized = new Set(values.map((value) => value.toLowerCase()));
	if (normalized.has("twelfth_student") && normalized.has("college_student")) {
		return "both";
	}
	if (normalized.has("twelfth_student")) return "twelfth";
	return "college";
}

function parseOptionalCgpa(value: string): number | null {
	const trimmed = value.trim();
	if (!trimmed) return null;
	const parsed = Number(trimmed);
	if (!Number.isFinite(parsed) || parsed < 0 || parsed > 10) {
		throw new Error("Minimum CGPA must be between 0 and 10.");
	}
	return parsed;
}

function splitUniqueCsv(value: string): string[] {
	const seen = new Set<string>();
	const items: string[] = [];
	for (const item of value.split(",")) {
		const trimmed = item.trim();
		const key = trimmed.toLowerCase();
		if (!trimmed || seen.has(key)) continue;
		seen.add(key);
		items.push(trimmed);
	}
	return items;
}

function stringList(value: unknown): string[] {
	if (!Array.isArray(value)) return [];
	return value.map((item) => String(item).trim()).filter(Boolean);
}
