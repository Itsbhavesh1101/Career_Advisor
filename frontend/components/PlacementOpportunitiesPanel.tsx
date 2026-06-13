"use client";

import type { FormEvent } from "react";
import { useCallback, useEffect, useId, useMemo, useState } from "react";
import {
	buttonClass,
	cn,
	DataTable,
	EmptyState,
	Field,
	FormSection,
	fieldControlClass,
	GlassPanel,
	StatusBadge,
} from "@/components/ui";
import {
	archivePlacementCompany,
	bulkShortlistPlacementStudents,
	bulkUpdatePlacementApplications,
	createPlacementAnnouncement,
	createPlacementCompany,
	createPlacementInterviewRound,
	createPlacementOpportunity,
	exportPlacementApplicationsCsv,
	exportPlacementOpportunitiesCsv,
	listAdminPlacementActivity,
	listAdminPlacementApplications,
	listAdminPlacementCompanies,
	listAdminPlacementOpportunities,
	listAdminPlacementUpcomingActions,
	listPlacementEligibleStudents,
	type NotificationAudience,
	type NotificationPriority,
	type PlacementActivityEventRead,
	type PlacementApplicationRead,
	type PlacementApplicationStatus,
	type PlacementCompanyRead,
	type PlacementEligibleStudentRead,
	type PlacementInterviewRoundCreate,
	type PlacementInterviewStatus,
	type PlacementOfferStatus,
	type PlacementOpportunityCreate,
	type PlacementOpportunityRead,
	type PlacementOpportunityStatus,
	type PlacementOpportunityType,
	type PlacementUpcomingActionRead,
	updatePlacementApplicationOffer,
	updatePlacementApplicationStatus,
	updatePlacementCompany,
	updatePlacementInterviewRound,
	updatePlacementOpportunity,
} from "@/lib/api";
import {
	applicationStatusLabels,
	buildApplicationStatusSummary,
	buildOpportunityReviewSummary,
	buildPlacementActivityLabel,
	buildUpcomingActionSummary,
	groupApplicationsByStatus,
} from "@/lib/placementAdminUi";
import {
	buildEligibilityFromControls,
	type EligibilityStudentTypeScope,
	formatEligibilityJson,
	hasAdvancedEligibilityKeys,
	type PlacementEligibilityControls,
	parseAdvancedEligibilityJson,
	parseEligibilityToControls,
} from "@/lib/placementEligibility";

const opportunityStatuses: PlacementOpportunityStatus[] = [
	"draft",
	"active",
	"closed",
	"archived",
];

const opportunityTypes: PlacementOpportunityType[] = [
	"placement",
	"internship",
];

const applicationStatuses: PlacementApplicationStatus[] = [
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

const interviewOutcomeStatuses: PlacementInterviewStatus[] = [
	"selected",
	"hold",
	"rejected",
	"no_show",
	"rescheduled",
	"completed",
	"cancelled",
];

const offerStatuses: PlacementOfferStatus[] = [
	"offered",
	"accepted",
	"declined",
	"withdrawn",
];

const offerStatusLabels: Record<PlacementOfferStatus, string> = {
	offered: "Offered",
	accepted: "Accepted",
	declined: "Declined",
	withdrawn: "Withdrawn",
};

type EligibilityMode = "guided" | "advanced";

interface OpportunityFormState {
	title: string;
	company: string;
	company_id: string;
	opportunity_type: PlacementOpportunityType;
	status: PlacementOpportunityStatus;
	deadline_at: string;
	location: string;
	work_mode: string;
	package_label: string;
	vacancies: string;
	contact_name: string;
	contact_email: string;
	hiring_stages: string;
	required_skills: string;
	eligibility_mode: EligibilityMode;
	eligibility_student_scope: EligibilityStudentTypeScope;
	eligibility_min_cgpa: string;
	eligibility_specializations: string;
	eligibility: string;
	description: string;
	apply_url: string;
}

interface CompanyFormState {
	name: string;
	website: string;
	industry: string;
	location: string;
	contact_name: string;
	contact_email: string;
	notes: string;
}

interface InterviewDraftState {
	round_name: string;
	scheduled_at: string;
	mode: string;
	location: string;
	interviewer: string;
	notes: string;
}

interface OfferDraftState {
	offer_status: PlacementOfferStatus;
	offer_role: string;
	offer_package: string;
	offer_location: string;
	offer_joining_date: string;
	offer_notes: string;
	next_step: string;
}

const defaultEligibilityControls: PlacementEligibilityControls = {
	studentTypeScope: "college",
	minCgpa: "",
	specializations: "",
};

function createEmptyForm(): OpportunityFormState {
	return {
		title: "",
		company: "",
		company_id: "",
		opportunity_type: "placement",
		status: "active",
		deadline_at: "",
		location: "",
		work_mode: "",
		package_label: "",
		vacancies: "",
		contact_name: "",
		contact_email: "",
		hiring_stages: "",
		required_skills: "",
		eligibility_mode: "guided",
		eligibility_student_scope: defaultEligibilityControls.studentTypeScope,
		eligibility_min_cgpa: defaultEligibilityControls.minCgpa,
		eligibility_specializations: defaultEligibilityControls.specializations,
		eligibility: formatEligibilityJson(
			buildEligibilityFromControls(defaultEligibilityControls),
		),
		description: "",
		apply_url: "",
	};
}

function createEmptyCompanyForm(): CompanyFormState {
	return {
		name: "",
		website: "",
		industry: "",
		location: "",
		contact_name: "",
		contact_email: "",
		notes: "",
	};
}

function createEmptyInterviewDraft(): InterviewDraftState {
	return {
		round_name: "",
		scheduled_at: "",
		mode: "",
		location: "",
		interviewer: "",
		notes: "",
	};
}

function createOfferDraft(
	application?: PlacementApplicationRead,
): OfferDraftState {
	return {
		offer_status: application?.offer_status ?? "offered",
		offer_role: application?.offer_role ?? "",
		offer_package: application?.offer_package ?? "",
		offer_location: application?.offer_location ?? "",
		offer_joining_date: application?.offer_joining_date
			? application.offer_joining_date.slice(0, 16)
			: "",
		offer_notes: application?.offer_notes ?? "",
		next_step: application?.next_step ?? "",
	};
}

export default function PlacementOpportunitiesPanel() {
	const titleId = useId();
	const companyId = useId();
	const companyMasterId = useId();
	const companyNameId = useId();
	const companyWebsiteId = useId();
	const companyIndustryId = useId();
	const companyLocationId = useId();
	const companyContactNameId = useId();
	const companyContactEmailId = useId();
	const companyNotesId = useId();
	const typeId = useId();
	const deadlineId = useId();
	const locationId = useId();
	const workModeId = useId();
	const packageLabelId = useId();
	const vacanciesId = useId();
	const contactNameId = useId();
	const contactEmailId = useId();
	const hiringStagesId = useId();
	const skillsId = useId();
	const eligibilityId = useId();
	const eligibilityScopeId = useId();
	const eligibilityMinCgpaId = useId();
	const eligibilitySpecializationsId = useId();
	const eligibilityModeId = useId();
	const descriptionId = useId();
	const applyUrlId = useId();
	const opportunityStatusFilterId = useId();
	const opportunityTypeFilterId = useId();
	const applicationOpportunityFilterId = useId();
	const applicationStatusFilterId = useId();
	const announcementTitleId = useId();
	const announcementAudienceId = useId();
	const announcementPriorityId = useId();
	const announcementMessageId = useId();
	const [opportunities, setOpportunities] = useState<
		PlacementOpportunityRead[]
	>([]);
	const [opportunityOptions, setOpportunityOptions] = useState<
		PlacementOpportunityRead[]
	>([]);
	const [applications, setApplications] = useState<PlacementApplicationRead[]>(
		[],
	);
	const [activity, setActivity] = useState<PlacementActivityEventRead[]>([]);
	const [upcomingActions, setUpcomingActions] = useState<
		PlacementUpcomingActionRead[]
	>([]);
	const [companies, setCompanies] = useState<PlacementCompanyRead[]>([]);
	const [eligibleStudents, setEligibleStudents] = useState<
		PlacementEligibleStudentRead[]
	>([]);
	const [editing, setEditing] = useState<PlacementOpportunityRead | null>(null);
	const [editingCompany, setEditingCompany] =
		useState<PlacementCompanyRead | null>(null);
	const [message, setMessage] = useState<string | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [loading, setLoading] = useState(true);
	const [saving, setSaving] = useState(false);
	const [savingApplicationId, setSavingApplicationId] = useState<number | null>(
		null,
	);
	const [savingCompany, setSavingCompany] = useState(false);
	const [sendingAnnouncement, setSendingAnnouncement] = useState(false);
	const [loadingShortlist, setLoadingShortlist] = useState(false);
	const [announcementForm, setAnnouncementForm] = useState<{
		title: string;
		message: string;
		audience: NotificationAudience;
		priority: NotificationPriority;
	}>({
		title: "",
		message: "",
		audience: "college_student",
		priority: "normal",
	});
	const [opportunityStatusFilter, setOpportunityStatusFilter] = useState<
		PlacementOpportunityStatus | ""
	>("");
	const [opportunityTypeFilter, setOpportunityTypeFilter] = useState<
		PlacementOpportunityType | ""
	>("");
	const [applicationOpportunityFilter, setApplicationOpportunityFilter] =
		useState("");
	const [applicationStatusFilter, setApplicationStatusFilter] = useState<
		PlacementApplicationStatus | ""
	>("");
	const [selectedOpportunityId, setSelectedOpportunityId] = useState<
		number | null
	>(null);
	const [selectedEligibleProfileIds, setSelectedEligibleProfileIds] = useState<
		number[]
	>([]);
	const [selectedApplicationIds, setSelectedApplicationIds] = useState<
		number[]
	>([]);
	const [bulkApplicationStatus, setBulkApplicationStatus] =
		useState<PlacementApplicationStatus>("shortlisted");
	const [bulkApplicationNextStep, setBulkApplicationNextStep] = useState("");
	const [bulkSaving, setBulkSaving] = useState(false);
	const [applicationNoteDrafts, setApplicationNoteDrafts] = useState<
		Record<number, string>
	>({});
	const [applicationNextStepDrafts, setApplicationNextStepDrafts] = useState<
		Record<number, string>
	>({});
	const [applicationNextStepDueDrafts, setApplicationNextStepDueDrafts] =
		useState<Record<number, string>>({});
	const [form, setForm] = useState<OpportunityFormState>(createEmptyForm);
	const [companyForm, setCompanyForm] = useState<CompanyFormState>(
		createEmptyCompanyForm,
	);
	const [interviewDrafts, setInterviewDrafts] = useState<
		Record<number, InterviewDraftState>
	>({});
	const [offerDrafts, setOfferDrafts] = useState<
		Record<number, OfferDraftState>
	>({});

	const opportunityFilters = useMemo(
		() => ({
			status: opportunityStatusFilter,
			opportunity_type: opportunityTypeFilter,
		}),
		[opportunityStatusFilter, opportunityTypeFilter],
	);

	const applicationFilters = useMemo(
		() => ({
			opportunity_id: applicationOpportunityFilter
				? Number(applicationOpportunityFilter)
				: undefined,
			status: applicationStatusFilter,
		}),
		[applicationOpportunityFilter, applicationStatusFilter],
	);
	const applicationSummary = useMemo(
		() => buildApplicationStatusSummary(applications),
		[applications],
	);
	const upcomingSummary = useMemo(
		() => buildUpcomingActionSummary(upcomingActions),
		[upcomingActions],
	);
	const applicationGroups = useMemo(
		() => groupApplicationsByStatus(applications),
		[applications],
	);
	const selectedOpportunity = useMemo(() => {
		if (!selectedOpportunityId) return null;
		return (
			opportunityOptions.find((item) => item.id === selectedOpportunityId) ??
			opportunities.find((item) => item.id === selectedOpportunityId) ??
			null
		);
	}, [opportunities, opportunityOptions, selectedOpportunityId]);
	const selectedOpportunitySummary = useMemo(
		() =>
			selectedOpportunity
				? buildOpportunityReviewSummary(selectedOpportunity, applications)
				: null,
		[selectedOpportunity, applications],
	);

	const load = useCallback(
		async function load() {
			setLoading(true);
			setError(null);
			try {
				const shouldLoadAllOpportunityOptions = Boolean(
					opportunityFilters.status || opportunityFilters.opportunity_type,
				);
				const [
					opportunityData,
					opportunityOptionData,
					applicationData,
					companyData,
					activityData,
					upcomingData,
				] = await Promise.all([
					listAdminPlacementOpportunities(opportunityFilters),
					shouldLoadAllOpportunityOptions
						? listAdminPlacementOpportunities()
						: Promise.resolve(null),
					listAdminPlacementApplications(applicationFilters),
					listAdminPlacementCompanies({ status: "active" }),
					listAdminPlacementActivity({ limit: 12 }),
					listAdminPlacementUpcomingActions(12),
				]);
				setOpportunities(opportunityData.items);
				setOpportunityOptions(
					opportunityOptionData?.items ?? opportunityData.items,
				);
				setApplications(applicationData.items);
				setCompanies(companyData.items);
				setActivity(activityData.items);
				setUpcomingActions(upcomingData.items);
				setApplicationNoteDrafts(
					Object.fromEntries(
						applicationData.items.map((item) => [
							item.id,
							item.admin_notes ?? "",
						]),
					),
				);
				setApplicationNextStepDrafts(
					Object.fromEntries(
						applicationData.items.map((item) => [
							item.id,
							item.next_step ?? "",
						]),
					),
				);
				setApplicationNextStepDueDrafts(
					Object.fromEntries(
						applicationData.items.map((item) => [
							item.id,
							item.next_step_due_at ? item.next_step_due_at.slice(0, 16) : "",
						]),
					),
				);
				setInterviewDrafts((current) =>
					Object.fromEntries(
						applicationData.items.map((item) => [
							item.id,
							current[item.id] ?? createEmptyInterviewDraft(),
						]),
					),
				);
				setOfferDrafts(
					Object.fromEntries(
						applicationData.items.map((item) => [
							item.id,
							createOfferDraft(item),
						]),
					),
				);
				setSelectedApplicationIds((current) =>
					current.filter((id) =>
						applicationData.items.some((item) => item.id === id),
					),
				);
			} catch (err) {
				setError(
					err instanceof Error
						? err.message
						: "Placement opportunities could not load.",
				);
			} finally {
				setLoading(false);
			}
		},
		[applicationFilters, opportunityFilters],
	);

	useEffect(() => {
		void load();
	}, [load]);

	useEffect(() => {
		const opportunityId = selectedOpportunityId;
		if (opportunityId === null) {
			setEligibleStudents([]);
			setSelectedEligibleProfileIds([]);
			return;
		}
		let cancelled = false;
		async function loadShortlist(id: number) {
			setLoadingShortlist(true);
			try {
				const data = await listPlacementEligibleStudents(id);
				if (!cancelled) {
					setEligibleStudents(data.items);
					setSelectedEligibleProfileIds((current) =>
						current.filter((profileId) =>
							data.items.some(
								(student) =>
									student.profile_id === profileId &&
									student.application_status !== "shortlisted",
							),
						),
					);
				}
			} catch {
				if (!cancelled) {
					setEligibleStudents([]);
				}
			} finally {
				if (!cancelled) {
					setLoadingShortlist(false);
				}
			}
		}
		void loadShortlist(opportunityId);
		return () => {
			cancelled = true;
		};
	}, [selectedOpportunityId]);

	function resetForm() {
		setEditing(null);
		setForm(createEmptyForm());
	}

	function resetCompanyForm() {
		setEditingCompany(null);
		setCompanyForm(createEmptyCompanyForm());
	}

	function reviewOpportunity(item: PlacementOpportunityRead) {
		setSelectedOpportunityId(item.id);
		setApplicationOpportunityFilter(String(item.id));
		setApplicationStatusFilter("");
	}

	function startEdit(item: PlacementOpportunityRead) {
		setEditing(item);
		const eligibility = item.eligibility ?? {};
		const controls = parseEligibilityToControls(eligibility);
		const useAdvancedEligibility = hasAdvancedEligibilityKeys(eligibility);
		setForm({
			title: item.title,
			company: item.company,
			company_id: item.company_id ? String(item.company_id) : "",
			opportunity_type: item.opportunity_type,
			status: item.status,
			deadline_at: item.deadline_at ? item.deadline_at.slice(0, 16) : "",
			location: item.location ?? "",
			work_mode: item.work_mode ?? "",
			package_label: item.package_label ?? "",
			vacancies:
				item.vacancies !== null && item.vacancies !== undefined
					? String(item.vacancies)
					: "",
			contact_name: item.contact_name ?? "",
			contact_email: item.contact_email ?? "",
			hiring_stages: item.hiring_stages.join(", "),
			required_skills: item.required_skills.join(", "),
			eligibility_mode: useAdvancedEligibility ? "advanced" : "guided",
			eligibility_student_scope: controls.studentTypeScope,
			eligibility_min_cgpa: controls.minCgpa,
			eligibility_specializations: controls.specializations,
			eligibility: JSON.stringify(item.eligibility ?? {}, null, 2),
			description: item.description ?? "",
			apply_url: item.apply_url ?? "",
		});
	}

	function selectCompanyForOpportunity(companyId: string) {
		const selected = companies.find((item) => String(item.id) === companyId);
		setForm({
			...form,
			company_id: companyId,
			company: selected?.name ?? form.company,
			location: selected?.location ?? form.location,
			contact_name: selected?.contact_name ?? form.contact_name,
			contact_email: selected?.contact_email ?? form.contact_email,
		});
	}

	function startEditCompany(company: PlacementCompanyRead) {
		setEditingCompany(company);
		setCompanyForm({
			name: company.name,
			website: company.website ?? "",
			industry: company.industry ?? "",
			location: company.location ?? "",
			contact_name: company.contact_name ?? "",
			contact_email: company.contact_email ?? "",
			notes: company.notes ?? "",
		});
	}

	function switchEligibilityMode(mode: EligibilityMode) {
		setMessage(null);
		setError(null);
		if (mode === "advanced") {
			try {
				const eligibility = buildEligibilityFromControls({
					studentTypeScope: form.eligibility_student_scope,
					minCgpa: form.eligibility_min_cgpa,
					specializations: form.eligibility_specializations,
				});
				setForm({
					...form,
					eligibility_mode: "advanced",
					eligibility: formatEligibilityJson(eligibility),
				});
			} catch (err) {
				setError(
					err instanceof Error
						? err.message
						: "Eligibility settings could not be converted.",
				);
			}
			return;
		}
		setForm({ ...form, eligibility_mode: "guided" });
	}

	function buildPayload(): PlacementOpportunityCreate {
		const eligibility =
			form.eligibility_mode === "advanced"
				? parseAdvancedEligibilityJson(form.eligibility)
				: buildEligibilityFromControls({
						studentTypeScope: form.eligibility_student_scope,
						minCgpa: form.eligibility_min_cgpa,
						specializations: form.eligibility_specializations,
					});
		return {
			title: form.title,
			company: form.company,
			company_id: form.company_id ? Number(form.company_id) : null,
			opportunity_type: form.opportunity_type,
			status: form.status,
			deadline_at: form.deadline_at
				? new Date(form.deadline_at).toISOString()
				: null,
			location: form.location.trim() || null,
			work_mode: form.work_mode.trim() || null,
			package_label: form.package_label.trim() || null,
			vacancies: form.vacancies.trim() ? Number(form.vacancies) : null,
			contact_name: form.contact_name.trim() || null,
			contact_email: form.contact_email.trim() || null,
			hiring_stages: form.hiring_stages
				.split(",")
				.map((stage) => stage.trim())
				.filter(Boolean),
			required_skills: form.required_skills
				.split(",")
				.map((skill) => skill.trim())
				.filter(Boolean),
			eligibility,
			description: form.description.trim() || null,
			apply_url: form.apply_url.trim() || null,
		};
	}

	async function handleSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setMessage(null);
		setError(null);
		setSaving(true);
		try {
			const payload = buildPayload();
			if (editing) {
				await updatePlacementOpportunity(editing.id, payload);
				setMessage("Placement opportunity updated.");
			} else {
				await createPlacementOpportunity(payload);
				setMessage("Placement opportunity added.");
			}
			resetForm();
			await load();
		} catch (err) {
			setError(
				err instanceof Error
					? err.message
					: "Placement opportunity could not save.",
			);
		} finally {
			setSaving(false);
		}
	}

	async function handleAnnouncementSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setMessage(null);
		setError(null);
		setSendingAnnouncement(true);
		try {
			const result = await createPlacementAnnouncement({
				title: announcementForm.title,
				message: announcementForm.message,
				audience: announcementForm.audience,
				priority: announcementForm.priority,
				action_url: "/internship",
			});
			setMessage(
				result.created_count
					? `Announcement sent to ${result.created_count} student workspace${result.created_count === 1 ? "" : "s"}.`
					: "No matching student workspaces were found for this announcement.",
			);
			setAnnouncementForm({
				title: "",
				message: "",
				audience: "college_student",
				priority: "normal",
			});
		} catch (err) {
			setError(
				err instanceof Error
					? err.message
					: "Placement announcement could not be sent.",
			);
		} finally {
			setSendingAnnouncement(false);
		}
	}

	async function handleCompanySubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setMessage(null);
		setError(null);
		setSavingCompany(true);
		try {
			const payload = {
				name: companyForm.name,
				website: companyForm.website.trim() || null,
				industry: companyForm.industry.trim() || null,
				location: companyForm.location.trim() || null,
				contact_name: companyForm.contact_name.trim() || null,
				contact_email: companyForm.contact_email.trim() || null,
				notes: companyForm.notes.trim() || null,
			};
			if (editingCompany) {
				await updatePlacementCompany(editingCompany.id, payload);
				setMessage("Placement company updated.");
			} else {
				await createPlacementCompany(payload);
				setMessage("Placement company added.");
			}
			resetCompanyForm();
			await load();
		} catch (err) {
			setError(
				err instanceof Error
					? err.message
					: "Placement company could not save.",
			);
		} finally {
			setSavingCompany(false);
		}
	}

	async function handleArchiveCompany(company: PlacementCompanyRead) {
		setMessage(null);
		setError(null);
		setSavingCompany(true);
		try {
			await archivePlacementCompany(company.id);
			await load();
			if (form.company_id === String(company.id)) {
				setForm({ ...form, company_id: "" });
			}
			if (editingCompany?.id === company.id) {
				resetCompanyForm();
			}
			setMessage("Placement company archived.");
		} catch (err) {
			setError(
				err instanceof Error
					? err.message
					: "Placement company could not archive.",
			);
		} finally {
			setSavingCompany(false);
		}
	}

	async function handleApplicationStatus(
		application: PlacementApplicationRead,
		status: PlacementApplicationStatus,
	) {
		setMessage(null);
		setError(null);
		setSavingApplicationId(application.id);
		try {
			await updatePlacementApplicationStatus(application.id, {
				status,
				admin_notes: applicationNoteDrafts[application.id]?.trim() || null,
				next_step: applicationNextStepDrafts[application.id]?.trim() || null,
				next_step_due_at: applicationNextStepDueDrafts[application.id]
					? new Date(applicationNextStepDueDrafts[application.id]).toISOString()
					: null,
			});
			await load();
			setMessage("Application status updated.");
		} catch (err) {
			setError(
				err instanceof Error ? err.message : "Application could not update.",
			);
		} finally {
			setSavingApplicationId(null);
		}
	}

	async function handleApplicationNoteSave(
		application: PlacementApplicationRead,
	) {
		setMessage(null);
		setError(null);
		setSavingApplicationId(application.id);
		try {
			await updatePlacementApplicationStatus(application.id, {
				status: application.status,
				admin_notes: applicationNoteDrafts[application.id]?.trim() || null,
				next_step: applicationNextStepDrafts[application.id]?.trim() || null,
				next_step_due_at: applicationNextStepDueDrafts[application.id]
					? new Date(applicationNextStepDueDrafts[application.id]).toISOString()
					: null,
			});
			await load();
			setMessage("Review note updated.");
		} catch (err) {
			setError(
				err instanceof Error ? err.message : "Review note could not update.",
			);
		} finally {
			setSavingApplicationId(null);
		}
	}

	function toggleEligibleProfile(profileId: number) {
		setSelectedEligibleProfileIds((current) =>
			current.includes(profileId)
				? current.filter((id) => id !== profileId)
				: [...current, profileId],
		);
	}

	function toggleApplication(applicationId: number) {
		setSelectedApplicationIds((current) =>
			current.includes(applicationId)
				? current.filter((id) => id !== applicationId)
				: [...current, applicationId],
		);
	}

	async function handleShortlistProfiles(profileIds: number[]) {
		if (!selectedOpportunityId || profileIds.length === 0) return;
		setMessage(null);
		setError(null);
		setBulkSaving(true);
		try {
			await bulkShortlistPlacementStudents(selectedOpportunityId, {
				profile_ids: profileIds,
				admin_notes: "Shortlisted from eligible-student review.",
				next_step: "Wait for placement-cell interview schedule.",
			});
			setSelectedEligibleProfileIds((current) =>
				current.filter((id) => !profileIds.includes(id)),
			);
			await load();
			const data = await listPlacementEligibleStudents(selectedOpportunityId);
			setEligibleStudents(data.items);
			setMessage(
				profileIds.length === 1
					? "Student shortlisted for this drive."
					: `${profileIds.length} students shortlisted for this drive.`,
			);
		} catch (err) {
			setError(
				err instanceof Error
					? err.message
					: "Students could not be shortlisted.",
			);
		} finally {
			setBulkSaving(false);
		}
	}

	async function handleBulkApplicationStatus() {
		if (selectedApplicationIds.length === 0) return;
		setMessage(null);
		setError(null);
		setBulkSaving(true);
		try {
			const payload = {
				application_ids: selectedApplicationIds,
				status: bulkApplicationStatus,
				...(bulkApplicationNextStep.trim()
					? { next_step: bulkApplicationNextStep.trim() }
					: {}),
			};
			await bulkUpdatePlacementApplications(payload);
			setSelectedApplicationIds([]);
			setBulkApplicationNextStep("");
			await load();
			setMessage("Selected applications updated.");
		} catch (err) {
			setError(
				err instanceof Error ? err.message : "Applications could not update.",
			);
		} finally {
			setBulkSaving(false);
		}
	}

	function updateInterviewDraft(
		applicationId: number,
		changes: Partial<InterviewDraftState>,
	) {
		setInterviewDrafts((current) => ({
			...current,
			[applicationId]: {
				...(current[applicationId] ?? createEmptyInterviewDraft()),
				...changes,
			},
		}));
	}

	function updateOfferDraft(
		applicationId: number,
		changes: Partial<OfferDraftState>,
	) {
		setOfferDrafts((current) => ({
			...current,
			[applicationId]: {
				...(current[applicationId] ?? createOfferDraft()),
				...changes,
			},
		}));
	}

	async function handleCreateInterview(application: PlacementApplicationRead) {
		const draft =
			interviewDrafts[application.id] ?? createEmptyInterviewDraft();
		if (!draft.round_name.trim()) {
			setError("Interview round name is required.");
			return;
		}
		setMessage(null);
		setError(null);
		setSavingApplicationId(application.id);
		try {
			const payload: PlacementInterviewRoundCreate = {
				round_name: draft.round_name.trim(),
				scheduled_at: draft.scheduled_at
					? new Date(draft.scheduled_at).toISOString()
					: null,
				mode: draft.mode.trim() || null,
				location: draft.location.trim() || null,
				interviewer: draft.interviewer.trim() || null,
				notes: draft.notes.trim() || null,
			};
			await createPlacementInterviewRound(application.id, payload);
			setInterviewDrafts((current) => ({
				...current,
				[application.id]: createEmptyInterviewDraft(),
			}));
			await load();
			setMessage("Interview round scheduled.");
		} catch (err) {
			setError(
				err instanceof Error
					? err.message
					: "Interview round could not be scheduled.",
			);
		} finally {
			setSavingApplicationId(null);
		}
	}

	async function handleInterviewOutcome(
		application: PlacementApplicationRead,
		interviewId: number,
		status: PlacementInterviewStatus,
	) {
		setMessage(null);
		setError(null);
		setSavingApplicationId(application.id);
		try {
			await updatePlacementInterviewRound(interviewId, { status });
			await load();
			setMessage("Interview outcome updated.");
		} catch (err) {
			setError(
				err instanceof Error
					? err.message
					: "Interview outcome could not update.",
			);
		} finally {
			setSavingApplicationId(null);
		}
	}

	async function handleOfferSave(application: PlacementApplicationRead) {
		const draft = offerDrafts[application.id] ?? createOfferDraft(application);
		setMessage(null);
		setError(null);
		setSavingApplicationId(application.id);
		try {
			await updatePlacementApplicationOffer(application.id, {
				offer_status: draft.offer_status,
				offer_role: draft.offer_role.trim() || null,
				offer_package: draft.offer_package.trim() || null,
				offer_location: draft.offer_location.trim() || null,
				offer_joining_date: draft.offer_joining_date
					? new Date(draft.offer_joining_date).toISOString()
					: null,
				offer_notes: draft.offer_notes.trim() || null,
				next_step: draft.next_step.trim() || null,
			});
			await load();
			setMessage("Offer details updated.");
		} catch (err) {
			setError(err instanceof Error ? err.message : "Offer could not update.");
		} finally {
			setSavingApplicationId(null);
		}
	}

	async function downloadCsv({
		filename,
		loadCsv,
	}: {
		filename: string;
		loadCsv: () => Promise<string>;
	}) {
		setError(null);
		try {
			const csv = await loadCsv();
			const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
			const url = URL.createObjectURL(blob);
			const link = document.createElement("a");
			link.href = url;
			link.download = filename;
			link.click();
			URL.revokeObjectURL(url);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Export failed.");
		}
	}

	const activeCount = opportunities.filter(
		(item) => item.status === "active",
	).length;
	const hasOpportunityFilters = Boolean(
		opportunityStatusFilter || opportunityTypeFilter,
	);
	const hasUnsavedNote = (application: PlacementApplicationRead) =>
		(applicationNoteDrafts[application.id] ?? "") !==
			(application.admin_notes ?? "") ||
		(applicationNextStepDrafts[application.id] ?? "") !==
			(application.next_step ?? "") ||
		(applicationNextStepDueDrafts[application.id] ?? "") !==
			(application.next_step_due_at
				? application.next_step_due_at.slice(0, 16)
				: "");

	return (
		<div className="space-y-5">
			<GlassPanel className="grid gap-5 p-6 lg:grid-cols-[0.9fr_1.1fr]">
				<div>
					<h2 className="text-2xl font-semibold text-zinc-950">
						Placement opportunities
					</h2>
					<p className="mt-2 text-sm leading-6 text-zinc-600">
						Publish internships and placement drives, track student interest,
						and keep this as a lightweight TnP workflow inside the command
						center.
					</p>
					<div className="mt-4 flex flex-wrap gap-2">
						<StatusBadge tone="orange">{activeCount} active</StatusBadge>
						<StatusBadge tone="neutral">
							{opportunities.length} opportunities shown
						</StatusBadge>
						<StatusBadge tone="neutral">
							{applications.length} applications shown
						</StatusBadge>
						<StatusBadge
							tone={applicationSummary.needsReview ? "warning" : "success"}
						>
							{applicationSummary.needsReview} need review
						</StatusBadge>
						<StatusBadge tone="neutral">
							{applicationSummary.activePipeline} active applicants
						</StatusBadge>
						<button
							type="button"
							onClick={() =>
								void downloadCsv({
									filename: "placement-opportunities.csv",
									loadCsv: () =>
										exportPlacementOpportunitiesCsv(opportunityFilters),
								})
							}
							className={buttonClass({
								variant: "secondary",
								className: "min-h-8 px-3 py-1 text-xs",
							})}
						>
							Export opportunities
						</button>
						<button
							type="button"
							onClick={() =>
								void downloadCsv({
									filename: "placement-applications.csv",
									loadCsv: () =>
										exportPlacementApplicationsCsv(applicationFilters),
								})
							}
							className={buttonClass({
								variant: "secondary",
								className: "min-h-8 px-3 py-1 text-xs",
							})}
						>
							Export applications
						</button>
					</div>
					{message ? (
						<p className="mt-4 rounded-lg border border-black/10 bg-white px-3 py-2 text-sm font-medium text-zinc-700">
							{message}
						</p>
					) : null}
					{error ? (
						<p className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-800">
							{error}
						</p>
					) : null}
				</div>

				<form onSubmit={handleSubmit} className="space-y-4">
					<FormSection
						title={editing ? "Edit opportunity" : "Add opportunity"}
						description="Create the drive with normal placement-cell controls. Advanced JSON is only for unusual constraints."
					>
						<div className="grid gap-3 md:grid-cols-2">
							<Field label="Title" htmlFor={titleId}>
								<input
									id={titleId}
									value={form.title}
									onChange={(event) =>
										setForm({ ...form, title: event.target.value })
									}
									className={fieldControlClass}
									placeholder="Backend Intern"
									required
								/>
							</Field>
							<Field
								label="Company master"
								htmlFor={companyMasterId}
								helper="Optional. Link this drive to a managed recruiter record."
							>
								<select
									id={companyMasterId}
									value={form.company_id}
									onChange={(event) =>
										selectCompanyForOpportunity(event.target.value)
									}
									className={fieldControlClass}
								>
									<option value="">No linked company</option>
									{companies.map((company) => (
										<option key={company.id} value={company.id}>
											{company.name}
										</option>
									))}
								</select>
							</Field>
							<Field label="Company" htmlFor={companyId}>
								<input
									id={companyId}
									value={form.company}
									onChange={(event) =>
										setForm({ ...form, company: event.target.value })
									}
									className={fieldControlClass}
									placeholder="Partner Tech"
									required
								/>
							</Field>
							<Field label="Type" htmlFor={typeId}>
								<select
									id={typeId}
									value={form.opportunity_type}
									onChange={(event) =>
										setForm({
											...form,
											opportunity_type: event.target
												.value as PlacementOpportunityType,
										})
									}
									className={fieldControlClass}
								>
									<option value="placement">Placement</option>
									<option value="internship">Internship</option>
								</select>
							</Field>
							<Field label="Deadline" htmlFor={deadlineId}>
								<input
									id={deadlineId}
									type="datetime-local"
									value={form.deadline_at}
									onChange={(event) =>
										setForm({ ...form, deadline_at: event.target.value })
									}
									className={fieldControlClass}
								/>
							</Field>
							<Field label="Location" htmlFor={locationId}>
								<input
									id={locationId}
									value={form.location}
									onChange={(event) =>
										setForm({ ...form, location: event.target.value })
									}
									className={fieldControlClass}
									placeholder="Bhopal / Remote"
								/>
							</Field>
							<Field label="Work mode" htmlFor={workModeId}>
								<input
									id={workModeId}
									value={form.work_mode}
									onChange={(event) =>
										setForm({ ...form, work_mode: event.target.value })
									}
									className={fieldControlClass}
									placeholder="On-site, remote, hybrid"
								/>
							</Field>
							<Field label="Package / stipend" htmlFor={packageLabelId}>
								<input
									id={packageLabelId}
									value={form.package_label}
									onChange={(event) =>
										setForm({ ...form, package_label: event.target.value })
									}
									className={fieldControlClass}
									placeholder="6 LPA / 15k stipend"
								/>
							</Field>
							<Field label="Vacancies" htmlFor={vacanciesId}>
								<input
									id={vacanciesId}
									type="number"
									min="0"
									step="1"
									value={form.vacancies}
									onChange={(event) =>
										setForm({ ...form, vacancies: event.target.value })
									}
									className={fieldControlClass}
									placeholder="20"
								/>
							</Field>
							<Field label="Contact name" htmlFor={contactNameId}>
								<input
									id={contactNameId}
									value={form.contact_name}
									onChange={(event) =>
										setForm({ ...form, contact_name: event.target.value })
									}
									className={fieldControlClass}
									placeholder="TnP coordinator"
								/>
							</Field>
							<Field label="Contact email" htmlFor={contactEmailId}>
								<input
									id={contactEmailId}
									type="email"
									value={form.contact_email}
									onChange={(event) =>
										setForm({ ...form, contact_email: event.target.value })
									}
									className={fieldControlClass}
									placeholder="placements@example.edu"
								/>
							</Field>
							<Field
								label="Hiring stages"
								htmlFor={hiringStagesId}
								helper="Comma-separated, shown in the admin review summary."
							>
								<input
									id={hiringStagesId}
									value={form.hiring_stages}
									onChange={(event) =>
										setForm({ ...form, hiring_stages: event.target.value })
									}
									className={fieldControlClass}
									placeholder="Screening, interview, offer"
								/>
							</Field>
							<Field label="Required skills" htmlFor={skillsId}>
								<input
									id={skillsId}
									value={form.required_skills}
									onChange={(event) =>
										setForm({
											...form,
											required_skills: event.target.value,
										})
									}
									className={fieldControlClass}
									placeholder="Python, SQL, Communication"
								/>
							</Field>
						</div>
						<div className="space-y-3 rounded-xl border border-black/10 bg-white p-4">
							<div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
								<div>
									<h4 className="text-sm font-semibold text-zinc-950">
										Eligibility
									</h4>
									<p className="mt-1 text-xs leading-5 text-zinc-500">
										Set who can see and apply for this opportunity without
										editing raw JSON.
									</p>
								</div>
								<label
									htmlFor={eligibilityModeId}
									className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-zinc-50 px-3 py-2 text-xs font-semibold text-zinc-700"
								>
									<input
										id={eligibilityModeId}
										type="checkbox"
										checked={form.eligibility_mode === "advanced"}
										onChange={(event) =>
											switchEligibilityMode(
												event.target.checked ? "advanced" : "guided",
											)
										}
										className="h-4 w-4 accent-orange-600"
									/>
									Advanced JSON
								</label>
							</div>
							<div className="grid gap-3 md:grid-cols-3">
								<Field label="Student audience" htmlFor={eligibilityScopeId}>
									<select
										id={eligibilityScopeId}
										value={form.eligibility_student_scope}
										onChange={(event) =>
											setForm({
												...form,
												eligibility_student_scope: event.target
													.value as EligibilityStudentTypeScope,
											})
										}
										disabled={form.eligibility_mode === "advanced"}
										className={fieldControlClass}
									>
										<option value="college">College students</option>
										<option value="twelfth">12th students</option>
										<option value="both">Both student paths</option>
									</select>
								</Field>
								<Field
									label="Minimum CGPA"
									htmlFor={eligibilityMinCgpaId}
									helper={
										form.eligibility_student_scope === "twelfth"
											? "Not used for 12th-only opportunities."
											: "Optional. Use 0 to 10 scale."
									}
								>
									<input
										id={eligibilityMinCgpaId}
										type="number"
										min="0"
										max="10"
										step="0.1"
										value={form.eligibility_min_cgpa}
										onChange={(event) =>
											setForm({
												...form,
												eligibility_min_cgpa: event.target.value,
											})
										}
										disabled={
											form.eligibility_mode === "advanced" ||
											form.eligibility_student_scope === "twelfth"
										}
										className={fieldControlClass}
										placeholder="7.0"
									/>
								</Field>
								<Field
									label="Specializations"
									htmlFor={eligibilitySpecializationsId}
									helper="Comma-separated. Leave blank for all branches."
								>
									<input
										id={eligibilitySpecializationsId}
										value={form.eligibility_specializations}
										onChange={(event) =>
											setForm({
												...form,
												eligibility_specializations: event.target.value,
											})
										}
										disabled={
											form.eligibility_mode === "advanced" ||
											form.eligibility_student_scope === "twelfth"
										}
										className={fieldControlClass}
										placeholder="CSE, AIML, Data Science"
									/>
								</Field>
							</div>
							{form.eligibility_mode === "advanced" ? (
								<Field
									label="Advanced eligibility JSON"
									htmlFor={eligibilityId}
									helper="Use only when the guided controls cannot express the rule."
								>
									<textarea
										id={eligibilityId}
										value={form.eligibility}
										onChange={(event) =>
											setForm({ ...form, eligibility: event.target.value })
										}
										className={`${fieldControlClass} min-h-24 font-mono`}
										spellCheck={false}
									/>
								</Field>
							) : (
								<p className="rounded-lg border border-orange-100 bg-orange-50 px-3 py-2 text-xs leading-5 text-orange-900">
									The saved rule will be generated from the audience, CGPA, and
									specialization controls.
								</p>
							)}
						</div>
						<Field label="Description" htmlFor={descriptionId}>
							<textarea
								id={descriptionId}
								value={form.description}
								onChange={(event) =>
									setForm({ ...form, description: event.target.value })
								}
								className={`${fieldControlClass} min-h-24`}
							/>
						</Field>
						<Field
							label="External apply URL"
							htmlFor={applyUrlId}
							helper="Optional. Students still track the application inside SAGE."
						>
							<input
								id={applyUrlId}
								type="url"
								value={form.apply_url}
								onChange={(event) =>
									setForm({ ...form, apply_url: event.target.value })
								}
								className={fieldControlClass}
								placeholder="https://company.example/apply"
							/>
						</Field>
						<div className="flex flex-wrap gap-2">
							<button
								type="submit"
								disabled={saving}
								className={buttonClass({ variant: "primary" })}
							>
								{saving
									? "Saving..."
									: editing
										? "Update opportunity"
										: "Add opportunity"}
							</button>
							{editing ? (
								<button
									type="button"
									onClick={resetForm}
									className={buttonClass({ variant: "secondary" })}
								>
									Cancel edit
								</button>
							) : null}
						</div>
					</FormSection>
				</form>
			</GlassPanel>

			<GlassPanel className="p-6">
				<form
					onSubmit={handleAnnouncementSubmit}
					className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr_auto]"
				>
					<div>
						<h3 className="text-lg font-semibold text-zinc-950">
							Notify students
						</h3>
						<p className="mt-1 text-sm leading-6 text-zinc-600">
							Send a focused in-app placement update to matching student
							workspaces.
						</p>
					</div>
					<div className="grid gap-3 md:grid-cols-2">
						<Field label="Title" htmlFor={announcementTitleId}>
							<input
								id={announcementTitleId}
								value={announcementForm.title}
								onChange={(event) =>
									setAnnouncementForm({
										...announcementForm,
										title: event.target.value,
									})
								}
								className={fieldControlClass}
								placeholder="Resume briefing tomorrow"
								required
							/>
						</Field>
						<div className="grid gap-3 sm:grid-cols-2">
							<Field label="Audience" htmlFor={announcementAudienceId}>
								<select
									id={announcementAudienceId}
									value={announcementForm.audience}
									onChange={(event) =>
										setAnnouncementForm({
											...announcementForm,
											audience: event.target.value as NotificationAudience,
										})
									}
									className={fieldControlClass}
								>
									<option value="college_student">College students</option>
									<option value="twelfth_student">12th students</option>
									<option value="all">All students</option>
								</select>
							</Field>
							<Field label="Priority" htmlFor={announcementPriorityId}>
								<select
									id={announcementPriorityId}
									value={announcementForm.priority}
									onChange={(event) =>
										setAnnouncementForm({
											...announcementForm,
											priority: event.target.value as NotificationPriority,
										})
									}
									className={fieldControlClass}
								>
									<option value="normal">Normal</option>
									<option value="high">High</option>
								</select>
							</Field>
						</div>
						<div className="md:col-span-2">
							<Field label="Message" htmlFor={announcementMessageId}>
								<textarea
									id={announcementMessageId}
									value={announcementForm.message}
									onChange={(event) =>
										setAnnouncementForm({
											...announcementForm,
											message: event.target.value,
										})
									}
									className={`${fieldControlClass} min-h-20`}
									placeholder="Share what students should prepare and when."
									required
								/>
							</Field>
						</div>
					</div>
					<div className="flex items-end">
						<button
							type="submit"
							disabled={sendingAnnouncement}
							className={buttonClass({
								variant: "primary",
								className: "w-full lg:w-auto",
							})}
						>
							{sendingAnnouncement ? "Sending..." : "Send update"}
						</button>
					</div>
				</form>
			</GlassPanel>

			<GlassPanel className="grid gap-5 p-6 lg:grid-cols-2">
				<div>
					<div className="flex flex-wrap items-start justify-between gap-3">
						<div>
							<h3 className="text-lg font-semibold text-zinc-950">
								Upcoming placement actions
							</h3>
							<p className="mt-1 text-sm leading-6 text-zinc-600">
								Deadlines, student next steps, interviews, and joining dates
								that need placement-cell follow-up.
							</p>
						</div>
						<StatusBadge tone={upcomingActions.length ? "orange" : "neutral"}>
							{upcomingSummary.nextActionLabel}
						</StatusBadge>
					</div>
					<div className="mt-4 divide-y divide-black/10 rounded-xl border border-black/10 bg-white/80">
						{upcomingActions.length ? (
							upcomingActions.slice(0, 6).map((action) => (
								<div
									key={`${action.action_type}-${action.application_id ?? action.opportunity_id ?? action.interview_round_id}-${action.due_at}`}
									className="grid gap-3 p-3 sm:grid-cols-[1fr_auto] sm:items-center"
								>
									<div>
										<div className="flex flex-wrap items-center gap-2">
											<p className="text-sm font-semibold text-zinc-950">
												{action.title}
											</p>
											<StatusBadge tone="neutral">
												{actionTypeLabel(action.action_type)}
											</StatusBadge>
										</div>
										<p className="mt-1 text-xs leading-5 text-zinc-500">
											{[
												action.student_name,
												action.opportunity_title,
												action.opportunity_company,
											]
												.filter(Boolean)
												.join(" - ") || "Placement board"}
										</p>
									</div>
									<p className="text-xs font-semibold text-zinc-700">
										{formatCompactDateTime(action.due_at)}
									</p>
								</div>
							))
						) : (
							<EmptyState
								title="No scheduled placement actions"
								description="Next steps, interviews, deadlines, and joining dates will appear here when drives move."
							/>
						)}
					</div>
				</div>

				<div>
					<div className="flex flex-wrap items-start justify-between gap-3">
						<div>
							<h3 className="text-lg font-semibold text-zinc-950">
								Recent placement activity
							</h3>
							<p className="mt-1 text-sm leading-6 text-zinc-600">
								A lightweight audit trail for drive, application, interview, and
								offer changes.
							</p>
						</div>
						<StatusBadge tone="neutral">{activity.length} recent</StatusBadge>
					</div>
					<div className="mt-4 divide-y divide-black/10 rounded-xl border border-black/10 bg-white/80">
						{activity.length ? (
							activity.slice(0, 6).map((item) => {
								const label = buildPlacementActivityLabel(item);
								return (
									<div
										key={item.id}
										className="grid gap-3 p-3 sm:grid-cols-[1fr_auto] sm:items-center"
									>
										<div>
											<p className="text-sm font-semibold text-zinc-950">
												{label.title}
											</p>
											<p className="mt-1 text-xs leading-5 text-zinc-500">
												{label.context}
											</p>
										</div>
										<p className="text-xs font-semibold text-zinc-700">
											{label.when}
										</p>
									</div>
								);
							})
						) : (
							<EmptyState
								title="No placement activity yet"
								description="Activity appears after drives, applications, interviews, or offers are updated."
							/>
						)}
					</div>
				</div>
			</GlassPanel>

			<GlassPanel className="space-y-4 p-6">
				<div className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
					<div>
						<h3 className="text-xl font-semibold text-zinc-950">
							Company master
						</h3>
						<p className="mt-1 text-sm leading-6 text-zinc-600">
							Maintain recruiter records once, then link them to internships and
							placement drives without retyping contact details.
						</p>
					</div>
					<StatusBadge tone="neutral">{companies.length} active</StatusBadge>
				</div>

				<div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
					<form onSubmit={handleCompanySubmit}>
						<FormSection
							title={editingCompany ? "Edit company" : "Add company"}
							description="Use neutral company metadata. Drive-specific details still live on the opportunity."
						>
							<div className="grid gap-3 md:grid-cols-2">
								<Field label="Company name" htmlFor={companyNameId}>
									<input
										id={companyNameId}
										value={companyForm.name}
										onChange={(event) =>
											setCompanyForm({
												...companyForm,
												name: event.target.value,
											})
										}
										className={fieldControlClass}
										placeholder="Partner Tech"
										required
									/>
								</Field>
								<Field label="Website" htmlFor={companyWebsiteId}>
									<input
										id={companyWebsiteId}
										type="url"
										value={companyForm.website}
										onChange={(event) =>
											setCompanyForm({
												...companyForm,
												website: event.target.value,
											})
										}
										className={fieldControlClass}
										placeholder="https://company.example"
									/>
								</Field>
								<Field label="Industry" htmlFor={companyIndustryId}>
									<input
										id={companyIndustryId}
										value={companyForm.industry}
										onChange={(event) =>
											setCompanyForm({
												...companyForm,
												industry: event.target.value,
											})
										}
										className={fieldControlClass}
										placeholder="IT services"
									/>
								</Field>
								<Field label="Location" htmlFor={companyLocationId}>
									<input
										id={companyLocationId}
										value={companyForm.location}
										onChange={(event) =>
											setCompanyForm({
												...companyForm,
												location: event.target.value,
											})
										}
										className={fieldControlClass}
										placeholder="Bhopal / Pune / Remote"
									/>
								</Field>
								<Field label="Contact name" htmlFor={companyContactNameId}>
									<input
										id={companyContactNameId}
										value={companyForm.contact_name}
										onChange={(event) =>
											setCompanyForm({
												...companyForm,
												contact_name: event.target.value,
											})
										}
										className={fieldControlClass}
										placeholder="Recruiter or HR contact"
									/>
								</Field>
								<Field label="Contact email" htmlFor={companyContactEmailId}>
									<input
										id={companyContactEmailId}
										type="email"
										value={companyForm.contact_email}
										onChange={(event) =>
											setCompanyForm({
												...companyForm,
												contact_email: event.target.value,
											})
										}
										className={fieldControlClass}
										placeholder="hr@company.example"
									/>
								</Field>
							</div>
							<Field label="Notes" htmlFor={companyNotesId}>
								<textarea
									id={companyNotesId}
									value={companyForm.notes}
									onChange={(event) =>
										setCompanyForm({
											...companyForm,
											notes: event.target.value,
										})
									}
									className={`${fieldControlClass} min-h-20`}
									placeholder="Relationship notes, hiring preferences, or follow-up context."
								/>
							</Field>
							<div className="flex flex-wrap gap-2">
								<button
									type="submit"
									disabled={savingCompany}
									className={buttonClass({
										variant: editingCompany ? "secondary" : "dark",
									})}
								>
									{savingCompany
										? "Saving..."
										: editingCompany
											? "Update company"
											: "Add company"}
								</button>
								{editingCompany ? (
									<button
										type="button"
										onClick={resetCompanyForm}
										className={buttonClass({ variant: "ghost" })}
									>
										Cancel edit
									</button>
								) : null}
							</div>
						</FormSection>
					</form>

					<div className="rounded-xl border border-black/10 bg-white/80">
						{companies.length ? (
							<div className="divide-y divide-black/5">
								{companies.map((company) => (
									<div
										key={company.id}
										className="grid gap-3 p-4 md:grid-cols-[1fr_auto] md:items-start"
									>
										<div>
											<div className="flex flex-wrap items-center gap-2">
												<p className="font-semibold text-zinc-950">
													{company.name}
												</p>
												<StatusBadge tone="neutral">
													{company.active_opportunity_count} active drives
												</StatusBadge>
											</div>
											<p className="mt-1 text-xs leading-5 text-zinc-500">
												{[
													company.industry,
													company.location,
													company.contact_email,
												]
													.filter(Boolean)
													.join(" - ") || "No company metadata yet"}
											</p>
											{company.notes ? (
												<p className="mt-2 rounded-lg border border-black/10 bg-zinc-50 px-3 py-2 text-xs leading-5 text-zinc-600">
													{company.notes}
												</p>
											) : null}
										</div>
										<div className="flex flex-wrap gap-2 md:justify-end">
											<button
												type="button"
												onClick={() =>
													selectCompanyForOpportunity(String(company.id))
												}
												className={buttonClass({
													variant: "secondary",
													className: "min-h-8 px-3 py-1 text-xs",
												})}
											>
												Use in form
											</button>
											<button
												type="button"
												onClick={() => startEditCompany(company)}
												className={buttonClass({
													variant: "ghost",
													className: "min-h-8 px-3 py-1 text-xs",
												})}
											>
												Edit
											</button>
											<button
												type="button"
												onClick={() => void handleArchiveCompany(company)}
												disabled={savingCompany}
												className={buttonClass({
													variant: "ghost",
													className:
														"min-h-8 px-3 py-1 text-xs text-red-700 hover:border-red-200 hover:bg-red-50",
												})}
											>
												Archive
											</button>
										</div>
									</div>
								))}
							</div>
						) : (
							<EmptyState
								title="No companies yet"
								description="Add recruiter companies here, then link them while creating drives."
							/>
						)}
					</div>
				</div>
			</GlassPanel>

			<GlassPanel className="space-y-4 p-6">
				<div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
					<div>
						<h3 className="text-xl font-semibold text-zinc-950">
							Opportunity board
						</h3>
						<p className="mt-1 text-sm text-zinc-600">
							Filter drives before reviewing, editing, or exporting the board.
						</p>
					</div>
					<div className="grid gap-2 sm:grid-cols-[minmax(0,160px)_minmax(0,160px)_auto] sm:items-end">
						<label
							htmlFor={opportunityStatusFilterId}
							className="space-y-1 text-xs font-semibold text-zinc-600"
						>
							<span>Status</span>
							<select
								id={opportunityStatusFilterId}
								value={opportunityStatusFilter}
								onChange={(event) =>
									setOpportunityStatusFilter(
										event.target.value as PlacementOpportunityStatus | "",
									)
								}
								className={`${fieldControlClass} min-h-9 py-1 text-xs`}
							>
								<option value="">All statuses</option>
								{opportunityStatuses.map((status) => (
									<option key={status} value={status}>
										{status}
									</option>
								))}
							</select>
						</label>
						<label
							htmlFor={opportunityTypeFilterId}
							className="space-y-1 text-xs font-semibold text-zinc-600"
						>
							<span>Type</span>
							<select
								id={opportunityTypeFilterId}
								value={opportunityTypeFilter}
								onChange={(event) =>
									setOpportunityTypeFilter(
										event.target.value as PlacementOpportunityType | "",
									)
								}
								className={`${fieldControlClass} min-h-9 py-1 text-xs`}
							>
								<option value="">All types</option>
								{opportunityTypes.map((type) => (
									<option key={type} value={type}>
										{type}
									</option>
								))}
							</select>
						</label>
						<button
							type="button"
							onClick={() => {
								setOpportunityStatusFilter("");
								setOpportunityTypeFilter("");
							}}
							disabled={!opportunityStatusFilter && !opportunityTypeFilter}
							className={buttonClass({
								variant: "secondary",
								className: "min-h-9 px-3 py-1 text-xs",
							})}
						>
							Clear filters
						</button>
					</div>
				</div>
				{loading ? (
					<p className="text-sm text-zinc-600">Loading opportunities...</p>
				) : null}
				{!loading && opportunities.length === 0 ? (
					<EmptyState
						title={
							hasOpportunityFilters
								? "No opportunities match these filters"
								: "No placement opportunities yet"
						}
						description={
							hasOpportunityFilters
								? "Clear the board filters to review every internship and placement drive."
								: "Add the first internship or placement drive above."
						}
					/>
				) : null}
				{opportunities.length ? (
					<DataTable>
						<thead className="border-b border-black/10 text-xs font-semibold text-zinc-500">
							<tr>
								<th className="px-4 py-3">Opportunity</th>
								<th className="px-4 py-3">Type</th>
								<th className="px-4 py-3">Status</th>
								<th className="px-4 py-3">Applicants</th>
								<th className="px-4 py-3">Actions</th>
							</tr>
						</thead>
						<tbody>
							{opportunities.map((item) => (
								<tr
									key={item.id}
									className={cn(
										"border-b border-black/5 last:border-0",
										selectedOpportunityId === item.id ? "bg-orange-50/70" : "",
									)}
								>
									<td className="px-4 py-3">
										<p className="font-semibold text-zinc-950">{item.title}</p>
										<p className="text-xs text-zinc-500">
											{item.company_master_name ?? item.company}
											{item.deadline_at
												? ` - closes ${formatDate(item.deadline_at)}`
												: ""}
										</p>
										{item.company_master_name &&
										item.company_master_name !== item.company ? (
											<p className="mt-1 text-[11px] text-zinc-400">
												Drive label: {item.company}
											</p>
										) : null}
									</td>
									<td className="px-4 py-3 capitalize">
										{item.opportunity_type}
									</td>
									<td className="px-4 py-3">
										<StatusBadge tone={statusTone(item.status)}>
											{item.status.replace("_", " ")}
										</StatusBadge>
									</td>
									<td className="px-4 py-3">{item.applicant_count}</td>
									<td className="px-4 py-3">
										<div className="flex flex-wrap gap-2">
											<button
												type="button"
												onClick={() => reviewOpportunity(item)}
												className={buttonClass({
													variant:
														selectedOpportunityId === item.id
															? "primary"
															: "secondary",
													className: "min-h-8 px-3 py-1 text-xs",
												})}
											>
												Review applicants
											</button>
											<button
												type="button"
												onClick={() => startEdit(item)}
												className={buttonClass({
													variant: "secondary",
													className: "min-h-8 px-3 py-1 text-xs",
												})}
											>
												Edit
											</button>
											{opportunityStatuses.map((status) => (
												<button
													key={status}
													type="button"
													onClick={() =>
														void updatePlacementOpportunity(item.id, {
															status,
														}).then(load)
													}
													disabled={item.status === status}
													className={buttonClass({
														variant: "ghost",
														className: "min-h-8 px-3 py-1 text-xs",
													})}
												>
													{status}
												</button>
											))}
										</div>
									</td>
								</tr>
							))}
						</tbody>
					</DataTable>
				) : null}
			</GlassPanel>

			{selectedOpportunity && selectedOpportunitySummary ? (
				<GlassPanel className="space-y-4 p-6" tone="orange">
					<div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
						<div>
							<div className="flex flex-wrap items-center gap-2">
								<h3 className="text-xl font-semibold text-zinc-950">
									{selectedOpportunitySummary.title}
								</h3>
								<StatusBadge tone={statusTone(selectedOpportunity.status)}>
									{selectedOpportunitySummary.status}
								</StatusBadge>
								<StatusBadge tone="neutral">
									{selectedOpportunitySummary.type}
								</StatusBadge>
							</div>
							<p className="mt-1 text-sm text-zinc-700">
								{selectedOpportunity.company_master_name ??
									selectedOpportunitySummary.company}{" "}
								- deadline {selectedOpportunitySummary.deadlineLabel}
							</p>
							{selectedOpportunity.company_master_name &&
							selectedOpportunity.company_master_name !==
								selectedOpportunitySummary.company ? (
								<p className="mt-1 text-xs text-zinc-500">
									Drive label: {selectedOpportunitySummary.company}
								</p>
							) : null}
							<p className="mt-2 text-xs leading-5 text-zinc-600">
								Skills: {selectedOpportunitySummary.requiredSkillsLabel}
							</p>
							<div className="mt-3 grid gap-2 text-xs text-zinc-600 sm:grid-cols-2 xl:grid-cols-4">
								<span className="rounded-lg border border-black/10 bg-white/80 px-3 py-2">
									Package: {selectedOpportunitySummary.packageLabel}
								</span>
								<span className="rounded-lg border border-black/10 bg-white/80 px-3 py-2">
									Vacancies: {selectedOpportunitySummary.vacanciesLabel}
								</span>
								<span className="rounded-lg border border-black/10 bg-white/80 px-3 py-2">
									Contact: {selectedOpportunitySummary.contactLabel}
								</span>
								<span className="rounded-lg border border-black/10 bg-white/80 px-3 py-2">
									Stages: {selectedOpportunitySummary.hiringStagesLabel}
								</span>
							</div>
						</div>
						<div className="flex flex-wrap gap-2">
							<StatusBadge
								tone={
									selectedOpportunitySummary.needsReview ? "warning" : "success"
								}
							>
								{selectedOpportunitySummary.needsReview} need review
							</StatusBadge>
							<StatusBadge tone="orange">
								{selectedOpportunitySummary.applicantCount} applicants
							</StatusBadge>
							<button
								type="button"
								onClick={() => startEdit(selectedOpportunity)}
								className={buttonClass({
									variant: "secondary",
									className: "min-h-8 px-3 py-1 text-xs",
								})}
							>
								Edit drive
							</button>
							<button
								type="button"
								onClick={() =>
									void downloadCsv({
										filename: `placement-applications-${selectedOpportunity.id}.csv`,
										loadCsv: () =>
											exportPlacementApplicationsCsv({
												opportunity_id: selectedOpportunity.id,
												status: applicationStatusFilter,
											}),
									})
								}
								className={buttonClass({
									variant: "secondary",
									className: "min-h-8 px-3 py-1 text-xs",
								})}
							>
								Export this drive
							</button>
							<button
								type="button"
								onClick={() => {
									setSelectedOpportunityId(null);
									setApplicationOpportunityFilter("");
								}}
								className={buttonClass({
									variant: "ghost",
									className: "min-h-8 px-3 py-1 text-xs",
								})}
							>
								Clear selection
							</button>
						</div>
					</div>
					<div className="rounded-xl border border-black/10 bg-white/85">
						<div className="flex flex-col gap-2 border-b border-black/10 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
							<div>
								<h4 className="text-sm font-semibold text-zinc-950">
									Eligible student shortlist
								</h4>
								<p className="mt-1 text-xs leading-5 text-zinc-500">
									Students matching this drive's audience and eligibility rules,
									ranked by required-skill overlap.
								</p>
							</div>
							<div className="flex flex-wrap items-center gap-2">
								<StatusBadge tone="neutral">
									{loadingShortlist
										? "Loading..."
										: `${eligibleStudents.length} eligible`}
								</StatusBadge>
								{selectedEligibleProfileIds.length ? (
									<button
										type="button"
										onClick={() =>
											void handleShortlistProfiles(selectedEligibleProfileIds)
										}
										disabled={bulkSaving}
										className={buttonClass({
											variant: "secondary",
											className: "min-h-8 px-3 py-1 text-xs",
										})}
									>
										Shortlist {selectedEligibleProfileIds.length}
									</button>
								) : null}
							</div>
						</div>
						{loadingShortlist ? (
							<p className="px-4 py-4 text-sm text-zinc-600">
								Loading eligible students...
							</p>
						) : eligibleStudents.length ? (
							<div className="divide-y divide-black/5">
								{eligibleStudents.slice(0, 8).map((student) => (
									<div
										key={student.profile_id}
										className="grid gap-3 px-4 py-3 lg:grid-cols-[1fr_auto_auto] lg:items-start"
									>
										<div>
											<div className="flex flex-wrap items-center gap-2">
												<input
													type="checkbox"
													checked={selectedEligibleProfileIds.includes(
														student.profile_id,
													)}
													onChange={() =>
														toggleEligibleProfile(student.profile_id)
													}
													disabled={!canShortlistStudent(student)}
													className="h-4 w-4 rounded border-black/20 text-orange-600 focus:ring-orange-500"
													aria-label={`Select ${student.student_name} for shortlist`}
												/>
												<p className="font-semibold text-zinc-950">
													{student.student_name}
												</p>
												<StatusBadge
													tone={studentMatchTone(student.match_score)}
												>
													{student.match_score}% match
												</StatusBadge>
												{student.application_status ? (
													<StatusBadge
														tone={applicationTone(student.application_status)}
													>
														{
															applicationStatusLabels[
																student.application_status
															]
														}
													</StatusBadge>
												) : (
													<StatusBadge tone="neutral">Not applied</StatusBadge>
												)}
											</div>
											<p className="mt-1 text-xs leading-5 text-zinc-500">
												{student.student_email ?? "No email"} -{" "}
												{student.specialization || "No specialization"} - CGPA{" "}
												{student.cgpa.toFixed(1)}
											</p>
											<p className="mt-2 text-xs leading-5 text-zinc-600">
												Matched:{" "}
												{student.matched_skills.length
													? student.matched_skills.join(", ")
													: "No required skills matched yet"}
											</p>
										</div>
										<div className="rounded-lg border border-black/10 bg-zinc-50 px-3 py-2 text-xs leading-5 text-zinc-600 lg:max-w-xs">
											<p className="font-semibold text-zinc-800">
												Missing skills
											</p>
											<p className="mt-1">
												{student.missing_skills.length
													? student.missing_skills.join(", ")
													: "No required-skill gaps"}
											</p>
										</div>
										<button
											type="button"
											onClick={() =>
												void handleShortlistProfiles([student.profile_id])
											}
											disabled={!canShortlistStudent(student) || bulkSaving}
											className={buttonClass({
												variant: "secondary",
												className: "min-h-8 px-3 py-1 text-xs",
											})}
										>
											Shortlist
										</button>
									</div>
								))}
								{eligibleStudents.length > 8 ? (
									<p className="px-4 py-3 text-xs text-zinc-500">
										Showing first 8 of {eligibleStudents.length}. Export
										applications after students apply.
									</p>
								) : null}
							</div>
						) : (
							<EmptyState
								title="No eligible students found"
								description="Adjust the drive eligibility or required skills if this opportunity should include a broader student set."
							/>
						)}
					</div>
				</GlassPanel>
			) : null}

			<GlassPanel className="space-y-4 p-6">
				<div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
					<div>
						<h3 className="text-xl font-semibold text-zinc-950">
							Student applications
						</h3>
						<p className="mt-1 text-sm text-zinc-600">
							Filter applicant rows by drive and status before review or CSV
							export.
						</p>
						<div className="mt-3 flex flex-wrap gap-2">
							<StatusBadge tone="neutral">
								{applicationSummary.total} shown
							</StatusBadge>
							<StatusBadge
								tone={applicationSummary.needsReview ? "warning" : "success"}
							>
								{applicationSummary.needsReview} need review
							</StatusBadge>
							<StatusBadge tone="orange">
								{applicationSummary.byStatus.applied} applied
							</StatusBadge>
							<StatusBadge tone="success">
								{applicationSummary.byStatus.shortlisted} shortlisted
							</StatusBadge>
						</div>
					</div>
					<div className="grid gap-2 sm:grid-cols-[minmax(0,220px)_minmax(0,180px)_auto] sm:items-end">
						<label
							htmlFor={applicationOpportunityFilterId}
							className="space-y-1 text-xs font-semibold text-zinc-600"
						>
							<span>Opportunity</span>
							<select
								id={applicationOpportunityFilterId}
								value={applicationOpportunityFilter}
								onChange={(event) => {
									setApplicationOpportunityFilter(event.target.value);
									setSelectedOpportunityId(
										event.target.value ? Number(event.target.value) : null,
									);
								}}
								className={`${fieldControlClass} min-h-9 py-1 text-xs`}
							>
								<option value="">All opportunities</option>
								{opportunityOptions.map((item) => (
									<option key={item.id} value={item.id}>
										{item.title}
									</option>
								))}
							</select>
						</label>
						<label
							htmlFor={applicationStatusFilterId}
							className="space-y-1 text-xs font-semibold text-zinc-600"
						>
							<span>Status</span>
							<select
								id={applicationStatusFilterId}
								value={applicationStatusFilter}
								onChange={(event) =>
									setApplicationStatusFilter(
										event.target.value as PlacementApplicationStatus | "",
									)
								}
								className={`${fieldControlClass} min-h-9 py-1 text-xs`}
							>
								<option value="">All statuses</option>
								{applicationStatuses.map((status) => (
									<option key={status} value={status}>
										{status.replace("_", " ")}
									</option>
								))}
							</select>
						</label>
						<button
							type="button"
							onClick={() => {
								setApplicationOpportunityFilter("");
								setApplicationStatusFilter("");
								setSelectedOpportunityId(null);
							}}
							disabled={
								!applicationOpportunityFilter && !applicationStatusFilter
							}
							className={buttonClass({
								variant: "secondary",
								className: "min-h-9 px-3 py-1 text-xs",
							})}
						>
							Clear filters
						</button>
					</div>
				</div>
				{applications.length ? (
					<div className="grid gap-2 rounded-xl border border-black/10 bg-zinc-50 p-3 lg:grid-cols-[auto_minmax(160px,220px)_minmax(200px,1fr)_auto] lg:items-end">
						<div>
							<p className="text-xs font-semibold text-zinc-700">Bulk update</p>
							<p className="mt-1 text-xs text-zinc-500">
								{selectedApplicationIds.length} selected
							</p>
						</div>
						<label className="space-y-1 text-xs font-semibold text-zinc-600">
							<span>Status</span>
							<select
								value={bulkApplicationStatus}
								onChange={(event) =>
									setBulkApplicationStatus(
										event.target.value as PlacementApplicationStatus,
									)
								}
								className={`${fieldControlClass} min-h-9 py-1 text-xs`}
							>
								{applicationStatuses.map((status) => (
									<option key={status} value={status}>
										{applicationStatusLabels[status]}
									</option>
								))}
							</select>
						</label>
						<label className="space-y-1 text-xs font-semibold text-zinc-600">
							<span>Next step</span>
							<input
								value={bulkApplicationNextStep}
								onChange={(event) =>
									setBulkApplicationNextStep(event.target.value)
								}
								className={`${fieldControlClass} min-h-9 py-1 text-xs`}
								placeholder="Optional shared instruction"
							/>
						</label>
						<button
							type="button"
							onClick={() => void handleBulkApplicationStatus()}
							disabled={!selectedApplicationIds.length || bulkSaving}
							className={buttonClass({
								variant: "secondary",
								className: "min-h-9 px-3 py-1 text-xs",
							})}
						>
							Apply to selected
						</button>
					</div>
				) : null}
				{applications.length ? (
					<div className="space-y-3">
						{applicationGroups.map((group) => (
							<div
								key={group.status}
								className="overflow-hidden rounded-xl border border-black/10 bg-white/75"
							>
								<div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/10 bg-zinc-50 px-4 py-3">
									<div className="flex flex-wrap items-center gap-2">
										<StatusBadge tone={applicationTone(group.status)}>
											{group.label}
										</StatusBadge>
										<p className="text-sm font-semibold text-zinc-800">
											{group.items.length} applicant
											{group.items.length === 1 ? "" : "s"}
										</p>
									</div>
									<p className="text-xs text-zinc-500">
										{applicationGroupHint(group.status)}
									</p>
								</div>
								<div className="divide-y divide-black/5">
									{group.items.map((application) => (
										<div
											key={application.id}
											className="grid gap-4 p-4 xl:grid-cols-[1fr_1fr_1.2fr_1.1fr] xl:items-start"
										>
											<div>
												<div className="flex items-center gap-2">
													<input
														type="checkbox"
														checked={selectedApplicationIds.includes(
															application.id,
														)}
														onChange={() => toggleApplication(application.id)}
														className="h-4 w-4 rounded border-black/20 text-orange-600 focus:ring-orange-500"
														aria-label={`Select application for ${application.student_name ?? "student"}`}
													/>
													<p className="font-semibold text-zinc-950">
														{application.student_name ?? "Student"}
													</p>
												</div>
												<p className="mt-1 text-xs text-zinc-500">
													{application.student_email ?? "No email"}
												</p>
												<p className="mt-2 text-xs text-zinc-500">
													Tracked {formatDate(application.created_at)}
												</p>
											</div>
											<div>
												<p className="font-medium text-zinc-900">
													{application.opportunity_title ?? "Opportunity"}
												</p>
												<p className="mt-1 text-xs text-zinc-500">
													{application.opportunity_company ?? "Placement cell"}
													{application.opportunity_type
														? ` - ${application.opportunity_type}`
														: ""}
												</p>
												{application.opportunity_id ? (
													<button
														type="button"
														onClick={() => {
															setSelectedOpportunityId(
																application.opportunity_id,
															);
															setApplicationOpportunityFilter(
																String(application.opportunity_id),
															);
														}}
														className={buttonClass({
															variant: "ghost",
															className: "mt-2 min-h-8 px-3 py-1 text-xs",
														})}
													>
														Focus drive
													</button>
												) : null}
											</div>
											<div className="space-y-2">
												<p className="rounded-lg border border-black/10 bg-zinc-50 px-3 py-2 text-xs leading-5 text-zinc-600">
													Student note:{" "}
													{application.interest_note || "No note."}
												</p>
												<label className="block space-y-1 text-xs font-semibold text-zinc-600">
													<span>Review note</span>
													<textarea
														value={applicationNoteDrafts[application.id] ?? ""}
														onChange={(event) =>
															setApplicationNoteDrafts((current) => ({
																...current,
																[application.id]: event.target.value,
															}))
														}
														className={`${fieldControlClass} min-h-20 py-2 text-xs`}
														placeholder="Screening note, interview update, or follow-up."
														aria-label={`Review note for ${application.student_name ?? "student"}`}
													/>
												</label>
												<label className="block space-y-1 text-xs font-semibold text-zinc-600">
													<span>Next student step</span>
													<textarea
														value={
															applicationNextStepDrafts[application.id] ?? ""
														}
														onChange={(event) =>
															setApplicationNextStepDrafts((current) => ({
																...current,
																[application.id]: event.target.value,
															}))
														}
														className={`${fieldControlClass} min-h-16 py-2 text-xs`}
														placeholder="Share the next action students should prepare for."
														aria-label={`Next step for ${application.student_name ?? "student"}`}
													/>
												</label>
												<label className="block space-y-1 text-xs font-semibold text-zinc-600">
													<span>Next step due</span>
													<input
														type="datetime-local"
														value={
															applicationNextStepDueDrafts[application.id] ?? ""
														}
														onChange={(event) =>
															setApplicationNextStepDueDrafts((current) => ({
																...current,
																[application.id]: event.target.value,
															}))
														}
														className={`${fieldControlClass} py-2 text-xs`}
														aria-label={`Next step due date for ${application.student_name ?? "student"}`}
													/>
												</label>
											</div>
											<div className="space-y-3">
												<div className="rounded-xl border border-black/10 bg-white/80 p-3">
													<p className="text-xs font-semibold text-zinc-700">
														Interview rounds
													</p>
													{application.interview_rounds?.length ? (
														<div className="mt-2 space-y-2">
															{application.interview_rounds.map((round) => (
																<div
																	key={round.id}
																	className="rounded-lg border border-black/10 bg-zinc-50 px-3 py-2 text-xs leading-5 text-zinc-600"
																>
																	<div className="flex flex-wrap items-center gap-2">
																		<span className="font-semibold text-zinc-900">
																			{round.round_name}
																		</span>
																		<StatusBadge
																			tone={
																				round.status === "completed"
																					? "success"
																					: round.status === "cancelled"
																						? "danger"
																						: "orange"
																			}
																		>
																			{round.status}
																		</StatusBadge>
																	</div>
																	<p className="mt-1">
																		{round.scheduled_at
																			? formatDateTime(round.scheduled_at)
																			: "Schedule pending"}
																		{round.mode ? ` - ${round.mode}` : ""}
																	</p>
																	{round.location || round.interviewer ? (
																		<p>
																			{[round.location, round.interviewer]
																				.filter(Boolean)
																				.join(" - ")}
																		</p>
																	) : null}
																	<div className="mt-2 flex flex-wrap gap-1">
																		{interviewOutcomeStatuses
																			.filter(
																				(status) => status !== round.status,
																			)
																			.map((status) => (
																				<button
																					key={status}
																					type="button"
																					onClick={() =>
																						void handleInterviewOutcome(
																							application,
																							round.id,
																							status,
																						)
																					}
																					disabled={
																						savingApplicationId ===
																						application.id
																					}
																					className={buttonClass({
																						variant: "ghost",
																						className:
																							"min-h-7 px-2 py-1 text-[11px]",
																					})}
																				>
																					{status.replace("_", " ")}
																				</button>
																			))}
																	</div>
																</div>
															))}
														</div>
													) : (
														<p className="mt-2 text-xs leading-5 text-zinc-500">
															No interview rounds scheduled.
														</p>
													)}
													<div className="mt-3 grid gap-2">
														<input
															value={
																interviewDrafts[application.id]?.round_name ??
																""
															}
															onChange={(event) =>
																updateInterviewDraft(application.id, {
																	round_name: event.target.value,
																})
															}
															className={`${fieldControlClass} min-h-8 py-1 text-xs`}
															placeholder="Round name"
															aria-label={`Interview round name for ${application.student_name ?? "student"}`}
														/>
														<input
															type="datetime-local"
															value={
																interviewDrafts[application.id]?.scheduled_at ??
																""
															}
															onChange={(event) =>
																updateInterviewDraft(application.id, {
																	scheduled_at: event.target.value,
																})
															}
															className={`${fieldControlClass} min-h-8 py-1 text-xs`}
															aria-label={`Interview schedule for ${application.student_name ?? "student"}`}
														/>
														<div className="grid gap-2 sm:grid-cols-2">
															<input
																value={
																	interviewDrafts[application.id]?.mode ?? ""
																}
																onChange={(event) =>
																	updateInterviewDraft(application.id, {
																		mode: event.target.value,
																	})
																}
																className={`${fieldControlClass} min-h-8 py-1 text-xs`}
																placeholder="Mode"
															/>
															<input
																value={
																	interviewDrafts[application.id]?.location ??
																	""
																}
																onChange={(event) =>
																	updateInterviewDraft(application.id, {
																		location: event.target.value,
																	})
																}
																className={`${fieldControlClass} min-h-8 py-1 text-xs`}
																placeholder="Venue or link"
															/>
														</div>
														<input
															value={
																interviewDrafts[application.id]?.interviewer ??
																""
															}
															onChange={(event) =>
																updateInterviewDraft(application.id, {
																	interviewer: event.target.value,
																})
															}
															className={`${fieldControlClass} min-h-8 py-1 text-xs`}
															placeholder="Interviewer or panel"
														/>
														<button
															type="button"
															onClick={() =>
																void handleCreateInterview(application)
															}
															disabled={savingApplicationId === application.id}
															className={buttonClass({
																variant: "secondary",
																className: "min-h-8 px-3 py-1 text-xs",
															})}
														>
															Schedule round
														</button>
													</div>
												</div>
												<div className="rounded-xl border border-black/10 bg-white/80 p-3">
													<div className="flex flex-wrap items-center justify-between gap-2">
														<p className="text-xs font-semibold text-zinc-700">
															Offer outcome
														</p>
														{application.offer_status ? (
															<StatusBadge
																tone={
																	application.offer_status === "accepted"
																		? "success"
																		: application.offer_status === "offered"
																			? "orange"
																			: "danger"
																}
															>
																{offerStatusLabels[application.offer_status]}
															</StatusBadge>
														) : null}
													</div>
													{application.offer_status ? (
														<div className="mt-2 rounded-lg border border-black/10 bg-zinc-50 px-3 py-2 text-xs leading-5 text-zinc-600">
															<p className="font-semibold text-zinc-900">
																{application.offer_role ?? "Role not listed"}
															</p>
															<p>
																{[
																	application.offer_package,
																	application.offer_location,
																	application.offer_joining_date
																		? `Joining ${formatDate(
																				application.offer_joining_date,
																			)}`
																		: null,
																]
																	.filter(Boolean)
																	.join(" - ") || "Offer details pending"}
															</p>
															{application.offer_notes ? (
																<p className="mt-1 text-zinc-500">
																	{application.offer_notes}
																</p>
															) : null}
														</div>
													) : (
														<p className="mt-2 text-xs leading-5 text-zinc-500">
															Record offer details once the recruiter selects
															this student.
														</p>
													)}
													<div className="mt-3 grid gap-2">
														<select
															value={
																offerDrafts[application.id]?.offer_status ??
																"offered"
															}
															onChange={(event) =>
																updateOfferDraft(application.id, {
																	offer_status: event.target
																		.value as PlacementOfferStatus,
																})
															}
															className={`${fieldControlClass} min-h-8 py-1 text-xs`}
															aria-label={`Offer status for ${application.student_name ?? "student"}`}
														>
															{offerStatuses.map((status) => (
																<option key={status} value={status}>
																	{offerStatusLabels[status]}
																</option>
															))}
														</select>
														<div className="grid gap-2 sm:grid-cols-2">
															<input
																value={
																	offerDrafts[application.id]?.offer_role ?? ""
																}
																onChange={(event) =>
																	updateOfferDraft(application.id, {
																		offer_role: event.target.value,
																	})
																}
																className={`${fieldControlClass} min-h-8 py-1 text-xs`}
																placeholder="Offer role"
															/>
															<input
																value={
																	offerDrafts[application.id]?.offer_package ??
																	""
																}
																onChange={(event) =>
																	updateOfferDraft(application.id, {
																		offer_package: event.target.value,
																	})
																}
																className={`${fieldControlClass} min-h-8 py-1 text-xs`}
																placeholder="Package"
															/>
														</div>
														<div className="grid gap-2 sm:grid-cols-2">
															<input
																value={
																	offerDrafts[application.id]?.offer_location ??
																	""
																}
																onChange={(event) =>
																	updateOfferDraft(application.id, {
																		offer_location: event.target.value,
																	})
																}
																className={`${fieldControlClass} min-h-8 py-1 text-xs`}
																placeholder="Location"
															/>
															<input
																type="datetime-local"
																value={
																	offerDrafts[application.id]
																		?.offer_joining_date ?? ""
																}
																onChange={(event) =>
																	updateOfferDraft(application.id, {
																		offer_joining_date: event.target.value,
																	})
																}
																className={`${fieldControlClass} min-h-8 py-1 text-xs`}
																aria-label={`Joining date for ${application.student_name ?? "student"}`}
															/>
														</div>
														<textarea
															value={
																offerDrafts[application.id]?.offer_notes ?? ""
															}
															onChange={(event) =>
																updateOfferDraft(application.id, {
																	offer_notes: event.target.value,
																})
															}
															className={`${fieldControlClass} min-h-16 py-2 text-xs`}
															placeholder="Offer notes or document requirements"
														/>
														<input
															value={
																offerDrafts[application.id]?.next_step ?? ""
															}
															onChange={(event) =>
																updateOfferDraft(application.id, {
																	next_step: event.target.value,
																})
															}
															className={`${fieldControlClass} min-h-8 py-1 text-xs`}
															placeholder="Student next action"
														/>
														<button
															type="button"
															onClick={() => void handleOfferSave(application)}
															disabled={savingApplicationId === application.id}
															className={buttonClass({
																variant: "secondary",
																className: "min-h-8 px-3 py-1 text-xs",
															})}
														>
															Save offer
														</button>
													</div>
												</div>
												<div className="flex flex-wrap gap-2">
													<button
														type="button"
														onClick={() =>
															void handleApplicationNoteSave(application)
														}
														disabled={
															savingApplicationId === application.id ||
															!hasUnsavedNote(application)
														}
														className={buttonClass({
															variant: "secondary",
															className: "min-h-8 px-3 py-1 text-xs",
														})}
													>
														{savingApplicationId === application.id
															? "Saving..."
															: "Save note"}
													</button>
													{applicationStatuses
														.filter((status) => status !== application.status)
														.map((status) => (
															<button
																key={status}
																type="button"
																onClick={() =>
																	void handleApplicationStatus(
																		application,
																		status,
																	)
																}
																disabled={
																	savingApplicationId === application.id
																}
																className={buttonClass({
																	variant:
																		status === "shortlisted" ||
																		status === "placed"
																			? "secondary"
																			: "ghost",
																	className: "min-h-8 px-3 py-1 text-xs",
																})}
															>
																{applicationStatusLabels[status]}
															</button>
														))}
												</div>
											</div>
										</div>
									))}
								</div>
							</div>
						))}
					</div>
				) : (
					<EmptyState
						title="No applications yet"
						description="Applications appear when students mark interest or apply from their internship/readiness loop."
					/>
				)}
			</GlassPanel>
		</div>
	);
}

function formatDate(value: string) {
	return new Intl.DateTimeFormat("en-IN", {
		day: "2-digit",
		month: "short",
	}).format(new Date(value));
}

function formatDateTime(value: string) {
	return new Intl.DateTimeFormat("en-IN", {
		day: "2-digit",
		month: "short",
		hour: "2-digit",
		minute: "2-digit",
	}).format(new Date(value));
}

function formatCompactDateTime(value: string) {
	return new Intl.DateTimeFormat("en-GB", {
		day: "2-digit",
		month: "short",
		hour: "2-digit",
		minute: "2-digit",
		hour12: false,
		timeZone: "UTC",
	}).format(new Date(value));
}

function actionTypeLabel(
	actionType: PlacementUpcomingActionRead["action_type"],
) {
	switch (actionType) {
		case "application_next_step":
			return "Next step";
		case "opportunity_deadline":
			return "Deadline";
		case "interview_round":
			return "Interview";
		case "offer_joining":
			return "Joining";
		default:
			return "Action";
	}
}

function statusTone(
	status: PlacementOpportunityStatus,
): "success" | "warning" | "neutral" | "danger" {
	if (status === "active") return "success";
	if (status === "draft") return "warning";
	if (status === "closed") return "neutral";
	return "danger";
}

function applicationTone(
	status: PlacementApplicationStatus,
): "success" | "warning" | "neutral" | "danger" | "orange" {
	if (
		status === "placed" ||
		status === "joined" ||
		status === "offer_made" ||
		status === "shortlisted"
	) {
		return "success";
	}
	if (status === "applied" || status === "interview_scheduled") return "orange";
	if (status === "not_selected" || status === "withdrawn") return "danger";
	if (status === "interested" || status === "screening") return "warning";
	return "neutral";
}

function studentMatchTone(score: number): "success" | "warning" | "neutral" {
	if (score >= 70) return "success";
	if (score >= 40) return "warning";
	return "neutral";
}

function canShortlistStudent(student: PlacementEligibleStudentRead) {
	return ![
		"shortlisted",
		"interview_scheduled",
		"offer_made",
		"placed",
		"joined",
		"not_selected",
	].includes(student.application_status ?? "");
}

function applicationGroupHint(status: PlacementApplicationStatus) {
	switch (status) {
		case "interested":
			return "New interest and fit notes";
		case "applied":
			return "Ready for screening";
		case "screening":
			return "Eligibility and resume review";
		case "shortlisted":
			return "Next round preparation";
		case "interview_scheduled":
			return "Interview coordination";
		case "offer_made":
			return "Offer and document follow-up";
		case "placed":
		case "joined":
			return "Completed placement outcome";
		case "not_selected":
		case "withdrawn":
			return "Closed applicant state";
		default:
			return "Applicant pipeline";
	}
}
