import type {
	PlacementActivityEventRead,
	PlacementApplicationRead,
	PlacementApplicationStatus,
	PlacementOpportunityRead,
	PlacementUpcomingActionRead,
	PlacementUpcomingActionType,
} from "@/lib/api";

export const applicationReviewOrder: PlacementApplicationStatus[] = [
	"interested",
	"applied",
	"screening",
	"shortlisted",
	"interview_scheduled",
	"offer_made",
	"placed",
	"joined",
	"not_selected",
	"withdrawn",
];

export const applicationStatusLabels: Record<
	PlacementApplicationStatus,
	string
> = {
	interested: "Interested",
	applied: "Applied",
	screening: "Screening",
	shortlisted: "Shortlisted",
	interview_scheduled: "Interview scheduled",
	offer_made: "Offer made",
	not_selected: "Not selected",
	placed: "Placed",
	joined: "Joined",
	withdrawn: "Withdrawn",
};

type ApplicationLike = Pick<
	PlacementApplicationRead,
	"status" | "admin_notes" | "opportunity_id"
>;

type OpportunityLike = Pick<
	PlacementOpportunityRead,
	| "id"
	| "title"
	| "company"
	| "opportunity_type"
	| "status"
	| "deadline_at"
	| "required_skills"
	| "applicant_count"
	| "package_label"
	| "vacancies"
	| "contact_name"
	| "contact_email"
	| "hiring_stages"
>;

export function buildApplicationStatusSummary(
	applications: readonly ApplicationLike[],
) {
	const byStatus = Object.fromEntries(
		applicationReviewOrder.map((status) => [status, 0]),
	) as Record<PlacementApplicationStatus, number>;
	let needsReview = 0;
	let activePipeline = 0;

	for (const application of applications) {
		byStatus[application.status] += 1;
		if (isReviewStatus(application.status)) activePipeline += 1;
		if (application.status === "interested" && !application.admin_notes) {
			needsReview += 1;
		}
	}

	return {
		total: applications.length,
		needsReview,
		activePipeline,
		byStatus,
	};
}

export function groupApplicationsByStatus<T extends ApplicationLike>(
	applications: readonly T[],
	{ includeEmpty = false }: { includeEmpty?: boolean } = {},
) {
	return applicationReviewOrder
		.map((status) => ({
			status,
			label: applicationStatusLabels[status],
			items: applications.filter(
				(application) => application.status === status,
			),
		}))
		.filter((group) => includeEmpty || group.items.length > 0);
}

export function buildOpportunityReviewSummary(
	opportunity: OpportunityLike,
	applications: readonly ApplicationLike[],
) {
	const related = applications.filter(
		(application) => application.opportunity_id === opportunity.id,
	);
	const summary = buildApplicationStatusSummary(related);
	return {
		title: opportunity.title,
		company: opportunity.company,
		status: opportunity.status,
		type: opportunity.opportunity_type,
		deadlineLabel: opportunity.deadline_at
			? formatDate(opportunity.deadline_at)
			: "No deadline",
		requiredSkillsLabel: opportunity.required_skills.length
			? opportunity.required_skills.join(", ")
			: "No required skills listed",
		packageLabel: opportunity.package_label ?? "Package not listed",
		vacanciesLabel:
			opportunity.vacancies !== null && opportunity.vacancies !== undefined
				? `${opportunity.vacancies} opening${opportunity.vacancies === 1 ? "" : "s"}`
				: "Vacancies not listed",
		contactLabel:
			[opportunity.contact_name, opportunity.contact_email]
				.map((value) => value?.trim())
				.filter(Boolean)
				.join(", ") || "Contact not listed",
		hiringStagesLabel: opportunity.hiring_stages.length
			? opportunity.hiring_stages.join(" -> ")
			: "Stages not listed",
		applicantCount: related.length || opportunity.applicant_count,
		needsReview: summary.needsReview,
	};
}

export function buildPlacementActivityLabel(
	activity: Pick<
		PlacementActivityEventRead,
		| "title"
		| "opportunity_title"
		| "opportunity_company"
		| "student_name"
		| "created_at"
	>,
) {
	return {
		title: activity.title,
		context:
			[
				activity.student_name,
				activity.opportunity_title,
				activity.opportunity_company,
			]
				.map((value) => value?.trim())
				.filter(Boolean)
				.join(" - ") || "Placement activity",
		when: formatDateTime(activity.created_at),
	};
}

export function buildUpcomingActionSummary(
	actions: readonly Pick<
		PlacementUpcomingActionRead,
		"action_type" | "due_at"
	>[],
) {
	const byType = {
		application_next_step: 0,
		interview_round: 0,
		offer_joining: 0,
		opportunity_deadline: 0,
	} satisfies Record<PlacementUpcomingActionType, number>;
	for (const action of actions) {
		byType[action.action_type] += 1;
	}
	const sorted = [...actions].sort(
		(left, right) =>
			new Date(left.due_at).getTime() - new Date(right.due_at).getTime(),
	);
	return {
		total: actions.length,
		nextActionLabel: sorted[0]
			? `Next action: ${formatDateTime(sorted[0].due_at)}`
			: "No scheduled actions",
		byType,
	};
}

function isReviewStatus(status: PlacementApplicationStatus) {
	return (
		status === "interested" ||
		status === "applied" ||
		status === "screening" ||
		status === "shortlisted" ||
		status === "interview_scheduled" ||
		status === "offer_made"
	);
}

function formatDate(value: string) {
	return new Intl.DateTimeFormat("en-GB", {
		day: "2-digit",
		month: "short",
		year: "numeric",
		timeZone: "UTC",
	}).format(new Date(value));
}

function formatDateTime(value: string) {
	return new Intl.DateTimeFormat("en-GB", {
		day: "2-digit",
		month: "short",
		hour: "2-digit",
		minute: "2-digit",
		hour12: false,
		timeZone: "UTC",
	}).format(new Date(value));
}
