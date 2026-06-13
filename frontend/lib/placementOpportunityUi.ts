import type {
	PlacementApplicationStatus,
	PlacementOpportunityRead,
	PlacementOpportunityType,
	PlacementUpcomingActionRead,
} from "@/lib/api";

type OpportunitySignal = Pick<
	PlacementOpportunityRead,
	| "match_score"
	| "matched_skills"
	| "required_skills"
	| "deadline_at"
	| "work_mode"
	| "location"
>;

type OpportunityMeta = {
	opportunity_type: PlacementOpportunityType;
	package_label?: string | null;
	vacancies?: number | null;
	work_mode?: string | null;
	location?: string | null;
	deadline_at?: string | null;
};

export function buildMatchReasons(opportunity: OpportunitySignal): string[] {
	const reasons: string[] = [];
	if (
		opportunity.match_score !== null &&
		opportunity.match_score !== undefined
	) {
		reasons.push(`${opportunity.match_score}% skill match`);
	}
	if (opportunity.matched_skills.length) {
		reasons.push(`Matched skills: ${opportunity.matched_skills.join(", ")}`);
	}
	const missingSkills = opportunity.required_skills.filter(
		(skill) =>
			!opportunity.matched_skills.some(
				(matched) => normalizeSkill(matched) === normalizeSkill(skill),
			),
	);
	if (missingSkills.length) {
		reasons.push(`Still build: ${missingSkills.slice(0, 3).join(", ")}`);
	}
	if (opportunity.deadline_at) {
		reasons.push(`Deadline: ${formatFullDate(opportunity.deadline_at)}`);
	}
	const modeAndLocation = [opportunity.work_mode, opportunity.location]
		.map((value) => value?.trim())
		.filter(Boolean)
		.join(" - ");
	if (modeAndLocation) reasons.push(modeAndLocation);
	return reasons;
}

export function buildOpportunityMeta(opportunity: OpportunityMeta): string[] {
	return [
		labelOpportunityType(opportunity.opportunity_type),
		opportunity.package_label,
		opportunity.vacancies !== null && opportunity.vacancies !== undefined
			? `${opportunity.vacancies} opening${opportunity.vacancies === 1 ? "" : "s"}`
			: null,
		opportunity.work_mode,
		opportunity.location,
		opportunity.deadline_at
			? `Deadline ${formatShortDate(opportunity.deadline_at)}`
			: null,
	]
		.map((value) => value?.trim())
		.filter(Boolean)
		.filter(
			(value, index, values) => values.indexOf(value) === index,
		) as string[];
}

export function buildApplicationNextStep(
	status: PlacementApplicationStatus,
): string {
	switch (status) {
		case "interested":
			return "Update your note or apply when your resume is ready.";
		case "applied":
			return "Track placement-cell updates and keep your resume evidence current.";
		case "screening":
			return "Your profile is under screening. Keep resume evidence and availability current.";
		case "shortlisted":
			return "Prepare for the next screening or interview round.";
		case "interview_scheduled":
			return "Prepare for the scheduled interview and keep documents ready.";
		case "offer_made":
			return "Review the offer, confirm documents, and wait for joining instructions.";
		case "placed":
			return "Placement marked. Keep documents and joining requirements ready.";
		case "joined":
			return "Joining is complete. Keep records updated with the placement cell.";
		case "not_selected":
			return "Review gaps, update readiness actions, and target the next fit.";
		case "withdrawn":
			return "This application is withdrawn. Use matched opportunities for another fit.";
		default:
			return "Track this application from your readiness loop.";
	}
}

export function canStudentEditApplicationNote(
	status: PlacementApplicationStatus,
): boolean {
	return status === "interested" || status === "applied";
}

export function canStudentWithdrawApplication(
	status: PlacementApplicationStatus,
): boolean {
	return (
		status !== "placed" &&
		status !== "joined" &&
		status !== "not_selected" &&
		status !== "withdrawn"
	);
}

export function isPlacementApplicationFinal(
	status: PlacementApplicationStatus,
): boolean {
	return (
		status === "placed" || status === "joined" || status === "not_selected"
	);
}

export function buildStudentPlacementActionLabel(
	action: Pick<
		PlacementUpcomingActionRead,
		"title" | "due_at" | "opportunity_title" | "opportunity_company"
	>,
) {
	return {
		title: action.title,
		context:
			[action.opportunity_title, action.opportunity_company]
				.map((value) => value?.trim())
				.filter(Boolean)
				.join(" - ") || "Placement action",
		when: formatDateTime(action.due_at),
	};
}

function labelOpportunityType(type: PlacementOpportunityType): string {
	return type === "internship" ? "Internship" : "Placement";
}

function formatFullDate(value: string): string {
	return new Intl.DateTimeFormat("en-GB", {
		day: "2-digit",
		month: "short",
		year: "numeric",
		timeZone: "UTC",
	}).format(new Date(value));
}

function formatShortDate(value: string): string {
	return new Intl.DateTimeFormat("en-GB", {
		day: "2-digit",
		month: "short",
		timeZone: "UTC",
	}).format(new Date(value));
}

function formatDateTime(value: string): string {
	return new Intl.DateTimeFormat("en-GB", {
		day: "2-digit",
		month: "short",
		hour: "2-digit",
		minute: "2-digit",
		hour12: false,
		timeZone: "UTC",
	}).format(new Date(value));
}

function normalizeSkill(value: string): string {
	return value.trim().toLowerCase();
}
