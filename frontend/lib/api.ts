import { toGentleAiMessage } from "@/lib/aiUx";
import { getSupabaseAccessToken } from "@/lib/supabaseAuth";

function isLoopbackHost(hostname: string): boolean {
	return hostname === "localhost" || hostname === "127.0.0.1";
}

function isHostedBrowser(): boolean {
	if (typeof window === "undefined") {
		return false;
	}

	return !isLoopbackHost(window.location.hostname);
}

function resolveApiBase(): string {
	const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
	if (configured) {
		if (typeof window !== "undefined") {
			try {
				const configuredUrl = new URL(configured);
				const browserHost = window.location.hostname;
				const loopbackHosts = new Set(["localhost", "127.0.0.1"]);
				const configuredIsLoopback = loopbackHosts.has(configuredUrl.hostname);
				const browserIsLoopback = loopbackHosts.has(browserHost);

				// Keep loopback hostname aligned so SameSite cookies are accepted.
				if (configuredIsLoopback && browserIsLoopback) {
					configuredUrl.hostname = browserHost;
					return configuredUrl.toString().replace(/\/+$/, "");
				}
			} catch {
				// Fall back to configured value when URL parsing fails.
			}
		}

		return configured.replace(/\/+$/, "");
	}

	if (isHostedBrowser()) {
		throw new Error(
			"Missing NEXT_PUBLIC_API_BASE_URL for hosted frontend. Configure it to the Cloud Run backend URL in your deployment environment.",
		);
	}

	// Keep frontend and backend on the same host to preserve cookie auth locally.
	if (typeof window !== "undefined") {
		const protocol = window.location.protocol === "https:" ? "https:" : "http:";
		return `${protocol}//${window.location.hostname}:8000`;
	}

	return "http://localhost:8000";
}
export type StudentType = "twelfth_student" | "college_student";

export type InstitutionBrandingMode = "sage" | "generic";

export interface InstitutionBranding {
	mode: InstitutionBrandingMode;
	product_name: string;
	institution_name: string;
	institution_short_name: string;
	homepage: Record<string, string>;
	auth: Record<string, string>;
	branch_guidance: Record<string, string>;
	placement_readiness: Record<string, string>;
	admin_command: Record<string, string>;
}

export type JsonValue =
	| string
	| number
	| boolean
	| null
	| { [key: string]: JsonValue }
	| JsonValue[];

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
	const apiBase = resolveApiBase();
	const headers = new Headers(options.headers ?? undefined);
	const hasBody = options.body !== undefined && options.body !== null;
	const isFormDataBody =
		typeof FormData !== "undefined" && options.body instanceof FormData;

	if (hasBody && !isFormDataBody && !headers.has("Content-Type")) {
		headers.set("Content-Type", "application/json");
	}
	if (!headers.has("Authorization")) {
		const token = await getSupabaseAccessToken();
		if (token) {
			headers.set("Authorization", `Bearer ${token}`);
		}
	}

	const response = await fetch(`${apiBase}${path}`, {
		credentials: "include",
		headers,
		...options,
	});

	if (!response.ok) {
		let message = "Request failed";
		try {
			const data = (await response.json()) as {
				detail?: string;
				error?: { message?: string };
			};
			message = data.error?.message || data.detail || message;
		} catch {}
		throw new Error(toGentleAiMessage(message));
	}

	return (await response.json()) as T;
}

async function requestText(
	path: string,
	options: RequestInit = {},
): Promise<string> {
	const apiBase = resolveApiBase();
	const headers = new Headers(options.headers ?? undefined);
	if (!headers.has("Authorization")) {
		const token = await getSupabaseAccessToken();
		if (token) {
			headers.set("Authorization", `Bearer ${token}`);
		}
	}

	const response = await fetch(`${apiBase}${path}`, {
		credentials: "include",
		headers,
		...options,
	});

	if (!response.ok) {
		throw new Error(toGentleAiMessage("Request failed"));
	}

	return response.text();
}

export interface StudentProfileCreate {
	name: string;
	twelfth_percentage: number | null;
	cgpa: number | null;
	degree: string | null;
	specialization: string | null;
	current_skills: string[];
	interests: string[];
	target_industry: string | null;
	projects: number;
	internships: number;
	certifications: number;
	subjects?: string[];
	math_strength?: string;
	logical_reasoning?: string;
	programming_interest?: string;
	user_type?: string;
}

export interface StudentProfileRead
	extends Omit<
		StudentProfileCreate,
		| "twelfth_percentage"
		| "cgpa"
		| "degree"
		| "specialization"
		| "target_industry"
	> {
	id: number;
	twelfth_percentage: number;
	cgpa: number;
	degree: string;
	specialization: string;
	target_industry: string;
	created_at: string;
}

export interface ResumeAnalysisRead {
	id: number;
	student_profile_id: number;
	file_name: string;
	extracted_skills: string[];
	projects: string[];
	experience: string[];
	education: string[];
	resume_score: number;
	missing_keywords: string[];
	weak_sections: string[];
	suggestions: string[];
	created_at: string;
}

export interface ProgramFitSummary {
	recommended_program_id: string;
	recommended_program_name: string;
	confidence: number;
	summary: string;
}

export interface ProgramRecommendation {
	program_id: string;
	program_name: string;
	school: string;
	fit_score: number;
	fit_level: "High" | "Medium" | "Low";
	reasons: string[];
	career_paths: string[];
	priority_skills: string[];
	first_year_focus: string[];
}

export interface ExpectationRealityCheck {
	expectation: string;
	reality: string;
	counselor_note: string;
}

export interface FirstYearRoadmapItem {
	term: string;
	focus: string[];
	evidence_to_build: string[];
}

export interface CounselorSummary {
	best_fit: string;
	risk_flags: string[];
	talking_points: string[];
	follow_up_questions: string[];
}

export interface RAGEvidence {
	chunk_id: string;
	source_title: string;
	source_type: string;
	excerpt: string;
	score: number;
	tags?: string[];
	program_ids?: string[];
	source_review_status?: string | null;
	source_freshness_status?: string | null;
}

export type RAGSourceType =
	| "program"
	| "counseling"
	| "placement"
	| "skill"
	| "resume"
	| "training"
	| "policy";

export type RAGSourceStatus = "active" | "inactive";
export type RAGReviewStatus = "pending_review" | "approved" | "rejected";

export interface RAGDocumentSourceCreate {
	title: string;
	source_type: RAGSourceType;
	tags: string[];
	program_ids: string[];
	text: string;
}

export interface RAGDocumentSourceUpload {
	title: string;
	source_type: RAGSourceType;
	tags: string[];
	program_ids: string[];
	file: File;
}

export interface RAGDocumentSourceRead {
	id: number;
	title: string;
	source_type: string;
	status: string;
	review_status: RAGReviewStatus;
	review_notes?: string | null;
	reviewed_by_user_id?: number | null;
	reviewed_at?: string | null;
	expires_at?: string | null;
	freshness_status: string;
	tags: string[];
	program_ids: string[];
	chunk_count: number;
	created_at: string;
	updated_at: string;
}

export interface RAGDocumentSourceList {
	items: RAGDocumentSourceRead[];
}

export interface RAGDocumentSourceStatusUpdate {
	status: RAGSourceStatus;
}

export interface RAGDocumentSourceReviewUpdate {
	review_status: RAGReviewStatus;
	review_notes?: string | null;
	expires_at?: string | null;
}

export interface CareerAnalysisRead {
	id: number;
	student_profile_id: number;
	career_recommendations: { role: string; score: number }[];
	skill_gaps: { skill: string; priority: string }[];
	learning_roadmap: { stage: string; topics: string[] }[];
	salary_insights: {
		currency: string;
		estimate_min: number;
		estimate_max: number;
	};
	industry_trends: { trend: string; impact: string }[];
	institution_config_version?: string | null;
	program_fit_summary?: ProgramFitSummary | null;
	program_recommendations?: ProgramRecommendation[] | null;
	expectation_reality_checks?: ExpectationRealityCheck[] | null;
	first_year_roadmap?: FirstYearRoadmapItem[] | null;
	counselor_summary?: CounselorSummary | null;
	rag_evidence?: RAGEvidence[];
	aiml_score?: number;
	cyber_security_score?: number;
	recommended_branch?: string;
	branch_reasoning?: { reason: string }[];
	aiml_roles?: { role: string; score: number }[];
	cyber_roles?: { role: string; score: number }[];
	aiml_skills?: string[];
	cyber_skills?: string[];
	aiml_roadmap?: { year: number; topics: string[] }[];
	cyber_roadmap?: { year: number; topics: string[] }[];
	industry_insights?: { branch: string; insight: string }[];
	created_at: string;
}

export interface EmployabilityScoreRead {
	id: number;
	student_profile_id: number;
	overall_score: number;
	academic_strength: number;
	technical_skills: number;
	industry_readiness: number;
	resume_quality: number;
	created_at: string;
}

export interface CompanyFitRead {
	id: number;
	student_profile_id: number;
	matches: {
		company: string;
		company_type?: string | null;
		target_roles?: string[];
		score: number;
		rationale?: string | null;
		matched_evidence?: string[];
		missing_requirements?: string[];
		preparation_plan?: string[];
		hiring_signal_summary?: string | null;
	}[];
	created_at: string;
}

export interface RoleGapRead {
	id: number;
	student_profile_id: number;
	role_gaps: {
		role: string;
		missing_skills: string[];
		learning_plan: string[];
		current_evidence?: string[];
		gap_reason?: string | null;
		next_project?: string | null;
		proof_to_build?: string[];
		priority?: string | null;
	}[];
	created_at: string;
}

export interface PlacementRiskRead {
	id: number;
	student_profile_id: number;
	risk_level: string;
	reasons: string[];
	created_at: string;
}

export interface AdminMetricsRead {
	total_profiles: number;
	total_students: number;
	placement_ready: number;
	needs_training: number;
	high_risk: number;
}

export interface AdminStudentRead {
	profile_id: number;
	user_id: number;
	name: string;
	user_type?: string | null;
	degree: string;
	specialization: string;
	cgpa: number;
	created_at: string;
	employability_score: number | null;
	placement_risk: string | null;
	has_analysis: boolean;
	has_resume: boolean;
	readiness_band: string;
}

export interface AdminStudentPageRead {
	items: AdminStudentRead[];
	total: number;
	page: number;
	page_size: number;
	total_pages: number;
}

export interface AdminReadinessSummaryRead {
	pending_rag_reviews: number;
	stale_rag_sources: number;
	failed_embeddings: number;
	chunks_without_embeddings: number;
	failed_analysis_jobs: number;
	missing_analysis: number;
	missing_resume: number;
}

export interface SystemReadinessRead {
	llm_provider: string;
	llm_configured: boolean;
	embedding_provider: string;
	embedding_configured: boolean;
	vector_search_enabled: boolean;
	celery_task_always_eager: boolean;
	failed_analysis_jobs: number;
	failed_embedding_jobs: number;
	pending_rag_reviews: number;
	stale_rag_sources: number;
	hints: string[];
}

export interface AdminSmokeDataCleanupPreviewRead {
	users: number;
	profiles: number;
	analysis_jobs: number;
	career_analyses: number;
	resume_analyses: number;
	employability_scores: number;
	placement_risks: number;
	company_fits: number;
	role_gap_analyses: number;
	internship_readiness: number;
	quiz_sessions: number;
	quiz_questions: number;
	quiz_answers: number;
	quiz_results: number;
	rag_sources: number;
	rag_chunks: number;
	sample_emails: string[];
	sample_rag_titles: string[];
}

export interface AdminSmokeDataCleanupResultRead
	extends AdminSmokeDataCleanupPreviewRead {
	deleted: boolean;
}

export type AdminManagedItemType =
	| "program"
	| "training_program"
	| "internship_opportunity"
	| "placement_company"
	| "institution_policy"
	| "knowledge_template"
	| "institution_content";

export type AdminManagedItemStatus = "active" | "inactive";

export interface AdminManagedItemRead {
	id: number;
	item_type: AdminManagedItemType;
	slug: string;
	title: string;
	summary?: string | null;
	status: AdminManagedItemStatus;
	payload: Record<string, JsonValue>;
	created_by_user_id?: number | null;
	updated_by_user_id?: number | null;
	created_at: string;
	updated_at: string;
}

export interface AdminManagedItemPageRead {
	items: AdminManagedItemRead[];
	total: number;
}

export interface AdminManagedItemCreate {
	item_type: AdminManagedItemType;
	slug: string;
	title: string;
	summary?: string | null;
	status?: AdminManagedItemStatus;
	payload?: Record<string, JsonValue>;
}

export interface AdminManagedItemUpdate {
	slug?: string;
	title?: string;
	summary?: string | null;
	status?: AdminManagedItemStatus;
	payload?: Record<string, JsonValue>;
}

export interface ManagedInternshipOpportunityRead {
	id: number;
	slug: string;
	title: string;
	summary?: string | null;
	company?: string | null;
	location?: string | null;
	duration?: string | null;
	skills: string[];
	eligibility: string[];
	apply_url?: string | null;
	deadline?: string | null;
	payload: Record<string, JsonValue>;
}

export interface ManagedInternshipOpportunityListRead {
	items: ManagedInternshipOpportunityRead[];
	total: number;
}

export type PlacementOpportunityType = "placement" | "internship";
export type PlacementOpportunityStatus =
	| "draft"
	| "active"
	| "closed"
	| "archived";
export type PlacementCompanyStatus = "active" | "archived";
export type PlacementApplicationStatus =
	| "interested"
	| "applied"
	| "screening"
	| "interview_scheduled"
	| "shortlisted"
	| "offer_made"
	| "not_selected"
	| "placed"
	| "joined"
	| "withdrawn";

export type PlacementInterviewStatus =
	| "scheduled"
	| "completed"
	| "cancelled"
	| "selected"
	| "rejected"
	| "hold"
	| "no_show"
	| "rescheduled";
export type PlacementOfferStatus =
	| "offered"
	| "accepted"
	| "declined"
	| "withdrawn";

export interface PlacementOpportunityRead {
	id: number;
	title: string;
	company: string;
	company_id?: number | null;
	opportunity_type: PlacementOpportunityType;
	status: PlacementOpportunityStatus;
	description?: string | null;
	location?: string | null;
	work_mode?: string | null;
	deadline_at?: string | null;
	eligibility: Record<string, JsonValue>;
	required_skills: string[];
	apply_url?: string | null;
	package_label?: string | null;
	vacancies?: number | null;
	contact_name?: string | null;
	contact_email?: string | null;
	hiring_stages: string[];
	created_by_user_id?: number | null;
	updated_by_user_id?: number | null;
	created_at: string;
	updated_at: string;
	applicant_count: number;
	match_score?: number | null;
	matched_skills: string[];
	application_status?: PlacementApplicationStatus | null;
	company_master_name?: string | null;
}

export interface PlacementOpportunityListRead {
	items: PlacementOpportunityRead[];
	total: number;
}

export interface PlacementOpportunityCreate {
	title: string;
	company: string;
	company_id?: number | null;
	opportunity_type: PlacementOpportunityType;
	status?: PlacementOpportunityStatus;
	description?: string | null;
	location?: string | null;
	work_mode?: string | null;
	deadline_at?: string | null;
	eligibility?: Record<string, JsonValue>;
	required_skills?: string[];
	apply_url?: string | null;
	package_label?: string | null;
	vacancies?: number | null;
	contact_name?: string | null;
	contact_email?: string | null;
	hiring_stages?: string[];
}

export type PlacementOpportunityUpdate = Partial<PlacementOpportunityCreate>;

export interface PlacementCompanyRead {
	id: number;
	name: string;
	status: PlacementCompanyStatus;
	website?: string | null;
	industry?: string | null;
	location?: string | null;
	contact_name?: string | null;
	contact_email?: string | null;
	notes?: string | null;
	created_by_user_id?: number | null;
	updated_by_user_id?: number | null;
	created_at: string;
	updated_at: string;
	active_opportunity_count: number;
}

export interface PlacementCompanyListRead {
	items: PlacementCompanyRead[];
	total: number;
}

export interface PlacementCompanyCreate {
	name: string;
	status?: PlacementCompanyStatus;
	website?: string | null;
	industry?: string | null;
	location?: string | null;
	contact_name?: string | null;
	contact_email?: string | null;
	notes?: string | null;
}

export type PlacementCompanyUpdate = Partial<PlacementCompanyCreate>;

export interface PlacementInterviewRoundRead {
	id: number;
	application_id: number;
	round_name: string;
	status: PlacementInterviewStatus;
	scheduled_at?: string | null;
	mode?: string | null;
	location?: string | null;
	interviewer?: string | null;
	notes?: string | null;
	created_by_user_id?: number | null;
	updated_by_user_id?: number | null;
	created_at: string;
	updated_at: string;
}

export interface PlacementInterviewRoundCreate {
	round_name: string;
	scheduled_at?: string | null;
	mode?: string | null;
	location?: string | null;
	interviewer?: string | null;
	notes?: string | null;
}

export type PlacementInterviewRoundUpdate =
	Partial<PlacementInterviewRoundCreate> & {
		status?: PlacementInterviewStatus;
	};

export interface PlacementApplicationRead {
	id: number;
	opportunity_id: number;
	profile_id: number;
	user_id: number;
	student_name?: string | null;
	student_email?: string | null;
	opportunity_title?: string | null;
	opportunity_company?: string | null;
	opportunity_type?: PlacementOpportunityType | null;
	status: PlacementApplicationStatus;
	interest_note?: string | null;
	admin_notes?: string | null;
	next_step?: string | null;
	next_step_due_at?: string | null;
	offer_status?: PlacementOfferStatus | null;
	offer_role?: string | null;
	offer_package?: string | null;
	offer_location?: string | null;
	offer_joining_date?: string | null;
	offer_notes?: string | null;
	offer_updated_by_user_id?: number | null;
	offer_updated_at?: string | null;
	interview_rounds: PlacementInterviewRoundRead[];
	created_at: string;
	updated_at: string;
}

export interface PlacementApplicationListRead {
	items: PlacementApplicationRead[];
	total: number;
}

export type PlacementUpcomingActionType =
	| "application_next_step"
	| "opportunity_deadline"
	| "interview_round"
	| "offer_joining";

export interface PlacementActivityEventRead {
	id: number;
	event_type: string;
	title: string;
	message?: string | null;
	opportunity_id?: number | null;
	application_id?: number | null;
	profile_id?: number | null;
	company_id?: number | null;
	actor_user_id?: number | null;
	opportunity_title?: string | null;
	opportunity_company?: string | null;
	student_name?: string | null;
	metadata: Record<string, JsonValue>;
	created_at: string;
}

export interface PlacementActivityEventListRead {
	items: PlacementActivityEventRead[];
	total: number;
}

export interface PlacementUpcomingActionRead {
	action_type: PlacementUpcomingActionType;
	title: string;
	due_at: string;
	opportunity_id?: number | null;
	application_id?: number | null;
	profile_id?: number | null;
	interview_round_id?: number | null;
	opportunity_title?: string | null;
	opportunity_company?: string | null;
	student_name?: string | null;
	status?: string | null;
}

export interface PlacementUpcomingActionListRead {
	items: PlacementUpcomingActionRead[];
	total: number;
}

export type NotificationPriority = "normal" | "high";
export type NotificationAudience =
	| "all"
	| "college_student"
	| "twelfth_student";

export interface NotificationRead {
	id: number;
	recipient_user_id: number;
	profile_id?: number | null;
	notification_type: string;
	title: string;
	message?: string | null;
	action_url?: string | null;
	priority: NotificationPriority;
	read_at?: string | null;
	created_by_user_id?: number | null;
	metadata: Record<string, JsonValue>;
	created_at: string;
}

export interface NotificationListRead {
	items: NotificationRead[];
	total: number;
	unread_count: number;
}

export interface NotificationMarkAllResult {
	updated_count: number;
}

export interface PlacementAnnouncementCreate {
	title: string;
	message: string;
	audience: NotificationAudience;
	action_url?: string | null;
	priority?: NotificationPriority;
}

export interface NotificationAnnouncementResult {
	created_count: number;
}

export interface PlacementEligibleStudentRead {
	profile_id: number;
	student_name: string;
	student_email?: string | null;
	specialization: string;
	cgpa: number;
	current_skills: string[];
	match_score: number;
	matched_skills: string[];
	missing_skills: string[];
	application_id?: number | null;
	application_status?: PlacementApplicationStatus | null;
}

export interface PlacementEligibleStudentListRead {
	items: PlacementEligibleStudentRead[];
	total: number;
}

export interface StudentDashboardSummaryRead {
	profile_id: number;
	student_type: string;
	profile_completeness: number;
	analysis_status: string;
	quiz_status: string;
	resume_status: string;
	readiness_summary: string;
	next_actions: string[];
}

export interface AdmissionMetricsRead {
	total_twelfth_profiles: number;
	analyzed_profiles: number;
	needs_analysis: number;
	high_intent: number;
	wrong_branch_risk: number;
	ready_for_counseling: number;
}

export interface AdmissionCounselorBriefRead {
	best_fit: string | null;
	confidence: number | null;
	talking_points: string[];
	expectation_checks: string[];
	first_year_actions: string[];
	evidence_titles: string[];
	follow_up_questions: string[];
}

export interface AdmissionLeadRead {
	profile_id: number;
	student_name: string;
	current_interest: string;
	preferred_stream: string;
	recommended_program: string | null;
	confidence: number | null;
	status: string;
	priority: string;
	lost_reason_signals: string[];
	counselor_brief: AdmissionCounselorBriefRead;
	created_at: string;
}

export interface AdmissionDashboardRead {
	metrics: AdmissionMetricsRead;
	leads: AdmissionLeadRead[];
}

export interface PlacementMetricsRead {
	total_college_profiles: number;
	placement_ready: number;
	needs_training: number;
	high_risk: number;
	company_ready: number;
	evidence_complete: number;
	average_employability: number | null;
}

export interface SkillEvidenceLedgerRead {
	evidence_score: number;
	project_count: number;
	internship_count: number;
	certification_count: number;
	resume_quality: number | null;
	internship_readiness: number | null;
	strengths: string[];
	gaps: string[];
}

export interface PlacementStudentSignalRead {
	profile_id: number;
	student_name: string;
	program: string;
	employability_score: number | null;
	placement_risk: string | null;
	top_company: string | null;
	top_company_score: number | null;
	status: string;
	priority: string;
	recommended_actions: string[];
	evidence: SkillEvidenceLedgerRead;
	created_at: string;
}

export interface CompanyReadinessRead {
	company: string;
	average_score: number;
	ready_count: number;
	watch_count: number;
	blocked_count: number;
	missing_skills: string[];
}

export interface TrainingROISignalRead {
	skill: string;
	affected_students: number;
	expected_readiness_lift: number;
	priority: string;
}

export interface FacultyAdvisorNoteRead {
	profile_id: number;
	student_name: string;
	escalation_level: string;
	focus_areas: string[];
	note: string;
}

export interface PlacementDashboardRead {
	metrics: PlacementMetricsRead;
	students: PlacementStudentSignalRead[];
	company_radar: CompanyReadinessRead[];
	training_roi: TrainingROISignalRead[];
	faculty_notes: FacultyAdvisorNoteRead[];
}

export interface TrainingRecommendationsRead {
	total_students: number;
	weak_skills: { skill: string; count: number }[];
	programs: { title: string; focus_skills: string[]; description: string }[];
}

export interface InternshipReadinessRead {
	id: number;
	student_profile_id: number;
	readiness_score: number;
	readiness_level: string;
	action_plan: string[];
	created_at: string;
}

export interface IndustryDemandRead {
	year: number;
	trends: { trend: string; impact: string }[];
}

export interface JobDispatchRead {
	job_id: string;
	status: "queued" | "running" | "completed" | "failed";
}

export interface AgentStageSummary {
	stage: string;
	label: string;
	status: "completed" | "skipped" | "failed";
	source: string;
	output_ref?: string | null;
	notes?: string[];
}

export interface SnapshotVerifierResult {
	status: "approved" | "approved_with_warnings" | "blocked";
	confidence: number;
	blockers: string[];
	warnings: string[];
	evidence_count: number;
	next_best_actions: string[];
}

export interface AnalysisSnapshotSummary {
	snapshot_version?: string;
	profile_id?: number;
	user_type?: string;
	career_analysis_id?: number;
	agent_stages?: AgentStageSummary[];
	verifier?: SnapshotVerifierResult;
}

export interface JobStatusRead {
	id: string;
	student_profile_id: number;
	status: "queued" | "running" | "completed" | "failed";
	progress: number;
	message: string | null;
	error: string | null;
	analysis_id: number | null;
	snapshot_summary: AnalysisSnapshotSummary | Record<string, unknown> | null;
	created_at: string;
	updated_at: string;
}

export interface JobStatusEnvelope {
	job: JobStatusRead;
}

export interface PsychometricQuestionOption {
	option_id: string;
	text: string;
	trait_effect: Record<string, number>;
}

export interface PsychometricQuestionRead {
	id: string;
	session_id: string;
	position: number;
	source: string;
	trait_tag?: string | null;
	question_text: string;
	options: PsychometricQuestionOption[];
	schema_version: string;
	prompt_version: string;
}

export interface PsychometricSessionStatusRead {
	session_id: string;
	status: "queued" | "in_progress" | "completed" | "failed";
	fallback_mode: boolean;
	breaker_open: boolean;
	ai_status:
		| "ai_generated"
		| "guided_adaptive"
		| "recovering"
		| "calibrating"
		| string;
	adaptation_reason?: string | null;
	next_focus?: string | null;
	questions_answered: number;
	min_questions: number;
	max_questions: number;
	confidence: number;
	current_traits: Record<string, number>;
	current_state: Record<string, JsonValue>;
	current_question: PsychometricQuestionRead | null;
	created_at: string;
	updated_at: string;
}

export interface PsychometricSessionStartRead {
	session: PsychometricSessionStatusRead;
}

export interface PsychometricAnswerSubmit {
	question_id: string;
	option_id: string;
	answer_id?: string;
	idempotency_key?: string;
	response_ms?: number;
}

export interface PsychometricAnswerRead {
	answer_id: string;
	accepted: boolean;
	duplicate: boolean;
	session: PsychometricSessionStatusRead;
}

export interface PsychometricResultRead {
	session_id: string;
	student_profile_id: number;
	user_id: number;
	trait_scores: Record<string, number>;
	confidence: number;
	question_count: number;
	fallback_count: number;
	trait_version: string;
	schema_version: string;
	prompt_version: string;
	scoring_config_hash: string;
	completed_at: string;
}

export type MeResponse = {
	email: string;
	role: string;
	student_type: StudentType;
};

export type ChatResponse = {
	response: string;
};

export async function getMe(): Promise<MeResponse> {
	return request<MeResponse>("/api/v1/auth/me");
}

export function sendChatMessage(
	profileId: number,
	message: string,
): Promise<ChatResponse> {
	return request<ChatResponse>(`/api/v1/chat/${profileId}`, {
		method: "POST",
		body: JSON.stringify({ message }),
	});
}

export function createProfile(
	payload: StudentProfileCreate,
): Promise<StudentProfileRead> {
	return request<StudentProfileRead>("/api/v1/profiles", {
		method: "POST",
		body: JSON.stringify(payload),
	});
}

export function getProfile(id: number): Promise<StudentProfileRead> {
	return request<StudentProfileRead>(`/api/v1/profiles/${id}`);
}

export function getProfileDashboardSummary(
	id: number,
): Promise<StudentDashboardSummaryRead> {
	return request<StudentDashboardSummaryRead>(
		`/api/v1/profiles/${id}/dashboard`,
	);
}

export function updateProfile(
	id: number,
	payload: StudentProfileCreate,
): Promise<StudentProfileRead> {
	return request<StudentProfileRead>(`/api/v1/profiles/${id}`, {
		method: "PUT",
		body: JSON.stringify(payload),
	});
}

export function listProfiles(): Promise<StudentProfileRead[]> {
	return request<StudentProfileRead[]>("/api/v1/profiles");
}

export function generateAnalysis(profileId: number): Promise<JobDispatchRead> {
	return request<JobDispatchRead>(`/api/v1/analysis/${profileId}`, {
		method: "POST",
	});
}

export function getJobStatus(jobId: string): Promise<JobStatusEnvelope> {
	return request<JobStatusEnvelope>(`/api/v1/jobs/${jobId}`);
}

export function startPsychometricQuiz(
	profileId: number,
): Promise<PsychometricSessionStartRead> {
	return request<PsychometricSessionStartRead>(
		`/api/v1/psychometric-quiz/start/${profileId}`,
		{
			method: "POST",
		},
	);
}

export function submitPsychometricAnswer(
	sessionId: string,
	payload: PsychometricAnswerSubmit,
): Promise<PsychometricAnswerRead> {
	return request<PsychometricAnswerRead>(
		`/api/v1/psychometric-quiz/${sessionId}/answer`,
		{
			method: "POST",
			body: JSON.stringify(payload),
		},
	);
}

export function getPsychometricQuizStatus(
	sessionId: string,
): Promise<PsychometricSessionStatusRead> {
	return request<PsychometricSessionStatusRead>(
		`/api/v1/psychometric-quiz/${sessionId}/status`,
	);
}

export function reportPsychometricQuizAbandonment(
	sessionId: string,
	reason = "navigation",
): Promise<PsychometricSessionStatusRead> {
	return request<PsychometricSessionStatusRead>(
		`/api/v1/psychometric-quiz/${sessionId}/abandon`,
		{
			method: "POST",
			keepalive: true,
			body: JSON.stringify({ reason }),
		},
	);
}

export function getPsychometricQuizResult(
	sessionId: string,
): Promise<PsychometricResultRead> {
	return request<PsychometricResultRead>(
		`/api/v1/psychometric-quiz/${sessionId}/result`,
	);
}

export function generateBranchAnalysis(
	profileId: number,
): Promise<CareerAnalysisRead> {
	return request<CareerAnalysisRead>(`/api/v1/branch-analysis/${profileId}`, {
		method: "POST",
	});
}

export function getAnalysis(profileId: number): Promise<CareerAnalysisRead> {
	return request<CareerAnalysisRead>(`/api/v1/analysis/${profileId}`);
}

export function getEmployabilityScore(
	profileId: number,
): Promise<EmployabilityScoreRead> {
	return request<EmployabilityScoreRead>(`/api/v1/employability/${profileId}`);
}

export function computeEmployabilityScore(
	profileId: number,
): Promise<EmployabilityScoreRead> {
	return request<EmployabilityScoreRead>(`/api/v1/employability/${profileId}`, {
		method: "POST",
	});
}

export function getCompanyFit(profileId: number): Promise<CompanyFitRead> {
	return request<CompanyFitRead>(`/api/v1/company-fit/${profileId}`);
}

export function generateCompanyFit(profileId: number): Promise<CompanyFitRead> {
	return request<CompanyFitRead>(`/api/v1/company-fit/${profileId}`, {
		method: "POST",
	});
}

export function getRoleGaps(profileId: number): Promise<RoleGapRead> {
	return request<RoleGapRead>(`/api/v1/role-gaps/${profileId}`);
}

export function generateRoleGaps(profileId: number): Promise<RoleGapRead> {
	return request<RoleGapRead>(`/api/v1/role-gaps/${profileId}`, {
		method: "POST",
	});
}

export function getPlacementRisk(
	profileId: number,
): Promise<PlacementRiskRead> {
	return request<PlacementRiskRead>(`/api/v1/placement-risk/${profileId}`);
}

export function generatePlacementRisk(
	profileId: number,
): Promise<PlacementRiskRead> {
	return request<PlacementRiskRead>(`/api/v1/placement-risk/${profileId}`, {
		method: "POST",
	});
}

export function getAdminMetrics(): Promise<AdminMetricsRead> {
	return request<AdminMetricsRead>("/api/v1/admin/metrics");
}

export function getAdminReadinessSummary(): Promise<AdminReadinessSummaryRead> {
	return request<AdminReadinessSummaryRead>("/api/v1/admin/readiness-summary");
}

export function getSystemReadiness(): Promise<SystemReadinessRead> {
	return request<SystemReadinessRead>("/api/v1/admin/system-readiness");
}

export function getAdminSmokeDataCleanupPreview(): Promise<AdminSmokeDataCleanupPreviewRead> {
	return request<AdminSmokeDataCleanupPreviewRead>(
		"/api/v1/admin/maintenance/smoke-data/preview",
	);
}

export function cleanupAdminSmokeData(
	confirm: string,
): Promise<AdminSmokeDataCleanupResultRead> {
	return request<AdminSmokeDataCleanupResultRead>(
		"/api/v1/admin/maintenance/smoke-data/cleanup",
		{
			method: "POST",
			body: JSON.stringify({ confirm }),
		},
	);
}

export function listAdminManagedItems(
	filters: {
		item_type?: AdminManagedItemType | "";
		status?: AdminManagedItemStatus | "";
	} = {},
): Promise<AdminManagedItemPageRead> {
	const params = new URLSearchParams();
	if (filters.item_type) {
		params.set("item_type", filters.item_type);
	}
	if (filters.status) {
		params.set("status", filters.status);
	}
	const query = params.toString();
	return request<AdminManagedItemPageRead>(
		`/api/v1/admin/management/items${query ? `?${query}` : ""}`,
	);
}

export function createAdminManagedItem(
	payload: AdminManagedItemCreate,
): Promise<AdminManagedItemRead> {
	return request<AdminManagedItemRead>("/api/v1/admin/management/items", {
		method: "POST",
		body: JSON.stringify(payload),
	});
}

export function updateAdminManagedItem(
	itemId: number,
	payload: AdminManagedItemUpdate,
): Promise<AdminManagedItemRead> {
	return request<AdminManagedItemRead>(
		`/api/v1/admin/management/items/${itemId}`,
		{
			method: "PATCH",
			body: JSON.stringify(payload),
		},
	);
}

export function archiveAdminManagedItem(
	itemId: number,
): Promise<AdminManagedItemRead> {
	return request<AdminManagedItemRead>(
		`/api/v1/admin/management/items/${itemId}`,
		{ method: "DELETE" },
	);
}

export function listAdminPlacementOpportunities(
	filters: {
		status?: PlacementOpportunityStatus | "";
		opportunity_type?: PlacementOpportunityType | "";
	} = {},
): Promise<PlacementOpportunityListRead> {
	const params = new URLSearchParams();
	if (filters.status) params.set("status", filters.status);
	if (filters.opportunity_type) {
		params.set("opportunity_type", filters.opportunity_type);
	}
	const query = params.toString();
	return request<PlacementOpportunityListRead>(
		`/api/v1/placement-opportunities/admin/opportunities${
			query ? `?${query}` : ""
		}`,
	);
}

export function listAdminPlacementCompanies(
	filters: { status?: PlacementCompanyStatus | ""; q?: string } = {},
): Promise<PlacementCompanyListRead> {
	const params = new URLSearchParams();
	if (filters.status) params.set("status", filters.status);
	if (filters.q?.trim()) params.set("q", filters.q.trim());
	const query = params.toString();
	return request<PlacementCompanyListRead>(
		`/api/v1/placement-opportunities/admin/companies${
			query ? `?${query}` : ""
		}`,
	);
}

export function createPlacementCompany(
	payload: PlacementCompanyCreate,
): Promise<PlacementCompanyRead> {
	return request<PlacementCompanyRead>(
		"/api/v1/placement-opportunities/admin/companies",
		{
			method: "POST",
			body: JSON.stringify(payload),
		},
	);
}

export function updatePlacementCompany(
	companyId: number,
	payload: PlacementCompanyUpdate,
): Promise<PlacementCompanyRead> {
	return request<PlacementCompanyRead>(
		`/api/v1/placement-opportunities/admin/companies/${companyId}`,
		{
			method: "PATCH",
			body: JSON.stringify(payload),
		},
	);
}

export function archivePlacementCompany(
	companyId: number,
): Promise<PlacementCompanyRead> {
	return request<PlacementCompanyRead>(
		`/api/v1/placement-opportunities/admin/companies/${companyId}`,
		{ method: "DELETE" },
	);
}

export function createPlacementOpportunity(
	payload: PlacementOpportunityCreate,
): Promise<PlacementOpportunityRead> {
	return request<PlacementOpportunityRead>(
		"/api/v1/placement-opportunities/admin/opportunities",
		{
			method: "POST",
			body: JSON.stringify(payload),
		},
	);
}

export function updatePlacementOpportunity(
	opportunityId: number,
	payload: PlacementOpportunityUpdate,
): Promise<PlacementOpportunityRead> {
	return request<PlacementOpportunityRead>(
		`/api/v1/placement-opportunities/admin/opportunities/${opportunityId}`,
		{
			method: "PATCH",
			body: JSON.stringify(payload),
		},
	);
}

export function listPlacementEligibleStudents(
	opportunityId: number,
): Promise<PlacementEligibleStudentListRead> {
	return request<PlacementEligibleStudentListRead>(
		`/api/v1/placement-opportunities/admin/opportunities/${opportunityId}/eligible-students`,
	);
}

export function bulkShortlistPlacementStudents(
	opportunityId: number,
	payload: {
		profile_ids: number[];
		admin_notes?: string | null;
		next_step?: string | null;
		next_step_due_at?: string | null;
	},
): Promise<PlacementApplicationListRead> {
	return request<PlacementApplicationListRead>(
		`/api/v1/placement-opportunities/admin/opportunities/${opportunityId}/shortlist`,
		{
			method: "POST",
			body: JSON.stringify(payload),
		},
	);
}

export function listAdminPlacementApplications(
	filters: {
		opportunity_id?: number;
		status?: PlacementApplicationStatus | "";
	} = {},
): Promise<PlacementApplicationListRead> {
	const params = new URLSearchParams();
	if (filters.opportunity_id) {
		params.set("opportunity_id", String(filters.opportunity_id));
	}
	if (filters.status) params.set("status", filters.status);
	const query = params.toString();
	return request<PlacementApplicationListRead>(
		`/api/v1/placement-opportunities/admin/applications${
			query ? `?${query}` : ""
		}`,
	);
}

export function listAdminPlacementActivity(
	filters: { opportunity_id?: number; limit?: number } = {},
): Promise<PlacementActivityEventListRead> {
	const params = new URLSearchParams();
	if (filters.opportunity_id) {
		params.set("opportunity_id", String(filters.opportunity_id));
	}
	if (filters.limit) params.set("limit", String(filters.limit));
	const query = params.toString();
	return request<PlacementActivityEventListRead>(
		`/api/v1/placement-opportunities/admin/activity${query ? `?${query}` : ""}`,
	);
}

export function listAdminPlacementUpcomingActions(
	limit = 50,
): Promise<PlacementUpcomingActionListRead> {
	return request<PlacementUpcomingActionListRead>(
		`/api/v1/placement-opportunities/admin/upcoming?limit=${limit}`,
	);
}

export function listNotifications(
	filters: { unread_only?: boolean; limit?: number } = {},
): Promise<NotificationListRead> {
	const params = new URLSearchParams();
	if (filters.unread_only) params.set("unread_only", "true");
	if (filters.limit) params.set("limit", String(filters.limit));
	const query = params.toString();
	return request<NotificationListRead>(
		`/api/v1/notifications${query ? `?${query}` : ""}`,
	);
}

export function markNotificationRead(
	notificationId: number,
): Promise<NotificationRead> {
	return request<NotificationRead>(
		`/api/v1/notifications/${notificationId}/read`,
		{ method: "POST" },
	);
}

export function markAllNotificationsRead(): Promise<NotificationMarkAllResult> {
	return request<NotificationMarkAllResult>("/api/v1/notifications/read-all", {
		method: "POST",
	});
}

export function createPlacementAnnouncement(
	payload: PlacementAnnouncementCreate,
): Promise<NotificationAnnouncementResult> {
	return request<NotificationAnnouncementResult>(
		"/api/v1/notifications/admin/placement-announcements",
		{
			method: "POST",
			body: JSON.stringify(payload),
		},
	);
}

export function updatePlacementApplicationStatus(
	applicationId: number,
	payload: {
		status: PlacementApplicationStatus;
		admin_notes?: string | null;
		next_step?: string | null;
		next_step_due_at?: string | null;
	},
): Promise<PlacementApplicationRead> {
	return request<PlacementApplicationRead>(
		`/api/v1/placement-opportunities/admin/applications/${applicationId}`,
		{
			method: "PATCH",
			body: JSON.stringify(payload),
		},
	);
}

export function bulkUpdatePlacementApplications(payload: {
	application_ids: number[];
	status: PlacementApplicationStatus;
	admin_notes?: string | null;
	next_step?: string | null;
	next_step_due_at?: string | null;
}): Promise<PlacementApplicationListRead> {
	return request<PlacementApplicationListRead>(
		"/api/v1/placement-opportunities/admin/applications/bulk",
		{
			method: "PATCH",
			body: JSON.stringify(payload),
		},
	);
}

export function createPlacementInterviewRound(
	applicationId: number,
	payload: PlacementInterviewRoundCreate,
): Promise<PlacementApplicationRead> {
	return request<PlacementApplicationRead>(
		`/api/v1/placement-opportunities/admin/applications/${applicationId}/interviews`,
		{
			method: "POST",
			body: JSON.stringify(payload),
		},
	);
}

export function updatePlacementInterviewRound(
	interviewId: number,
	payload: PlacementInterviewRoundUpdate,
): Promise<PlacementInterviewRoundRead> {
	return request<PlacementInterviewRoundRead>(
		`/api/v1/placement-opportunities/admin/interviews/${interviewId}`,
		{
			method: "PATCH",
			body: JSON.stringify(payload),
		},
	);
}

export function updatePlacementApplicationOffer(
	applicationId: number,
	payload: {
		offer_status: PlacementOfferStatus;
		offer_role?: string | null;
		offer_package?: string | null;
		offer_location?: string | null;
		offer_joining_date?: string | null;
		offer_notes?: string | null;
		next_step?: string | null;
		next_step_due_at?: string | null;
	},
): Promise<PlacementApplicationRead> {
	return request<PlacementApplicationRead>(
		`/api/v1/placement-opportunities/admin/applications/${applicationId}/offer`,
		{
			method: "PATCH",
			body: JSON.stringify(payload),
		},
	);
}

export function exportPlacementOpportunitiesCsv(
	filters: {
		status?: PlacementOpportunityStatus | "";
		opportunity_type?: PlacementOpportunityType | "";
	} = {},
): Promise<string> {
	const params = new URLSearchParams();
	if (filters.status) params.set("status", filters.status);
	if (filters.opportunity_type) {
		params.set("opportunity_type", filters.opportunity_type);
	}
	const query = params.toString();
	return requestText(
		`/api/v1/placement-opportunities/admin/export.csv${
			query ? `?${query}` : ""
		}`,
	);
}

export function exportPlacementApplicationsCsv(
	filters: {
		opportunity_id?: number;
		status?: PlacementApplicationStatus | "";
	} = {},
): Promise<string> {
	const params = new URLSearchParams();
	if (filters.opportunity_id) {
		params.set("opportunity_id", String(filters.opportunity_id));
	}
	if (filters.status) params.set("status", filters.status);
	const query = params.toString();
	return requestText(
		`/api/v1/placement-opportunities/admin/applications/export.csv${
			query ? `?${query}` : ""
		}`,
	);
}

export function listStudentPlacementOpportunities(
	profileId: number,
): Promise<PlacementOpportunityListRead> {
	return request<PlacementOpportunityListRead>(
		`/api/v1/placement-opportunities?profile_id=${profileId}`,
	);
}

export function listStudentPlacementApplications(
	profileId: number,
): Promise<PlacementApplicationListRead> {
	return request<PlacementApplicationListRead>(
		`/api/v1/placement-opportunities/applications?profile_id=${profileId}`,
	);
}

export function listStudentPlacementActivity(
	profileId: number,
	limit = 50,
): Promise<PlacementActivityEventListRead> {
	return request<PlacementActivityEventListRead>(
		`/api/v1/placement-opportunities/activity?profile_id=${profileId}&limit=${limit}`,
	);
}

export function listStudentPlacementUpcomingActions(
	profileId: number,
	limit = 50,
): Promise<PlacementUpcomingActionListRead> {
	return request<PlacementUpcomingActionListRead>(
		`/api/v1/placement-opportunities/upcoming?profile_id=${profileId}&limit=${limit}`,
	);
}

export function applyToPlacementOpportunity(
	opportunityId: number,
	payload: {
		profile_id: number;
		status?: "interested" | "applied";
		interest_note?: string | null;
	},
): Promise<PlacementApplicationRead> {
	return request<PlacementApplicationRead>(
		`/api/v1/placement-opportunities/${opportunityId}/apply`,
		{
			method: "POST",
			body: JSON.stringify(payload),
		},
	);
}

export function updateStudentPlacementApplication(
	applicationId: number,
	payload: {
		status: "interested" | "applied" | "withdrawn";
		interest_note?: string | null;
	},
): Promise<PlacementApplicationRead> {
	return request<PlacementApplicationRead>(
		`/api/v1/placement-opportunities/applications/${applicationId}`,
		{
			method: "PATCH",
			body: JSON.stringify(payload),
		},
	);
}

export function listRagSources(): Promise<RAGDocumentSourceList> {
	return request<RAGDocumentSourceList>("/api/v1/rag/admin/sources");
}

export function getInstitutionBranding(): Promise<InstitutionBranding> {
	return request<InstitutionBranding>("/api/v1/institution/branding");
}

export function createRagSource(
	payload: RAGDocumentSourceCreate,
): Promise<RAGDocumentSourceRead> {
	return request<RAGDocumentSourceRead>("/api/v1/rag/admin/sources", {
		method: "POST",
		body: JSON.stringify(payload),
	});
}

export function uploadRagSourceFile(
	payload: RAGDocumentSourceUpload,
): Promise<RAGDocumentSourceRead> {
	const body = new FormData();
	body.append("title", payload.title);
	body.append("source_type", payload.source_type);
	body.append("tags", payload.tags.join(","));
	body.append("program_ids", payload.program_ids.join(","));
	body.append("file", payload.file);

	return request<RAGDocumentSourceRead>("/api/v1/rag/admin/sources/upload", {
		method: "POST",
		body,
	});
}

export function updateRagSourceStatus(
	sourceId: number,
	status: RAGSourceStatus,
): Promise<RAGDocumentSourceRead> {
	return request<RAGDocumentSourceRead>(
		`/api/v1/rag/admin/sources/${sourceId}/status`,
		{
			method: "PATCH",
			body: JSON.stringify({ status } satisfies RAGDocumentSourceStatusUpdate),
		},
	);
}

export function updateRagSourceReview(
	sourceId: number,
	payload: RAGDocumentSourceReviewUpdate,
): Promise<RAGDocumentSourceRead> {
	return request<RAGDocumentSourceRead>(
		`/api/v1/rag/admin/sources/${sourceId}/review`,
		{
			method: "PATCH",
			body: JSON.stringify(payload),
		},
	);
}

export function listAdminStudents(
	page = 1,
	pageSize = 25,
	filters: Record<string, string | boolean | undefined> = {},
): Promise<AdminStudentPageRead> {
	const params = new URLSearchParams({
		page: String(page),
		page_size: String(pageSize),
	});
	for (const [key, value] of Object.entries(filters)) {
		if (value !== undefined && value !== "") {
			params.set(key, String(value));
		}
	}
	return request<AdminStudentPageRead>(
		`/api/v1/admin/students?${params.toString()}`,
	);
}

export function getAdminStudentsExportUrl(
	filters: Record<string, string | boolean | undefined> = {},
): string {
	const apiBase = resolveApiBase();
	const params = new URLSearchParams();
	for (const [key, value] of Object.entries(filters)) {
		if (value !== undefined && value !== "") {
			params.set(key, String(value));
		}
	}
	const query = params.toString();
	return `${apiBase}/api/v1/admin/students/export${query ? `?${query}` : ""}`;
}

export function getAdmissionIntelligenceDashboard(
	limit = 12,
): Promise<AdmissionDashboardRead> {
	return request<AdmissionDashboardRead>(
		`/api/v1/admission-intelligence/dashboard?limit=${limit}`,
	);
}

export function getPlacementIntelligenceDashboard(
	limit = 12,
): Promise<PlacementDashboardRead> {
	return request<PlacementDashboardRead>(
		`/api/v1/placement-intelligence/dashboard?limit=${limit}`,
	);
}

export function getTrainingRecommendations(): Promise<TrainingRecommendationsRead> {
	return request<TrainingRecommendationsRead>(
		"/api/v1/training/recommendations",
	);
}

export function getInternshipReadiness(
	profileId: number,
): Promise<InternshipReadinessRead> {
	return request<InternshipReadinessRead>(
		`/api/v1/internship-readiness/${profileId}`,
	);
}

export function generateInternshipReadiness(
	profileId: number,
): Promise<InternshipReadinessRead> {
	return request<InternshipReadinessRead>(
		`/api/v1/internship-readiness/${profileId}`,
		{
			method: "POST",
		},
	);
}

export function listManagedInternshipOpportunities(
	profileId: number,
): Promise<ManagedInternshipOpportunityListRead> {
	return request<ManagedInternshipOpportunityListRead>(
		`/api/v1/internship-readiness/${profileId}/managed-opportunities`,
	);
}

export function getIndustryDemand(): Promise<IndustryDemandRead> {
	return request<IndustryDemandRead>("/api/v1/industry-demand");
}

export async function submitResumeUrl(
	profileId: number,
	resumeUrl: string,
): Promise<ResumeAnalysisRead> {
	return request<ResumeAnalysisRead>(`/api/v1/resume/${profileId}`, {
		method: "POST",
		body: JSON.stringify({ resume_url: resumeUrl }),
	});
}

export function getResumeAnalysis(
	profileId: number,
): Promise<ResumeAnalysisRead> {
	return request<ResumeAnalysisRead>(`/api/v1/resume/${profileId}`);
}

export function formatINR(value: number) {
	const lakhs = value / 100000;
	return `INR ${lakhs.toFixed(1)}L`;
}
