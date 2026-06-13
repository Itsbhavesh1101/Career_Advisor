import type { InstitutionBranding } from "@/lib/api";

export const DEFAULT_BRANDING: InstitutionBranding = {
	mode: "sage",
	product_name: "SAGE Career Navigator",
	institution_name: "SAGE Group of Institutions",
	institution_short_name: "SAGE/SIRT",
	homepage: {
		headline: "SAGE Career Navigator",
		description:
			"Choose the right academic path, build placement readiness, and keep every recommendation connected to the student's goals, strengths, and next action.",
		feature_intro:
			"SAGE combines student intake, AI analysis, personalized copilot support, and practical readiness tools in the same workflow.",
	},
	auth: {
		signup_title: "Create your SAGE workspace",
		login_title: "Continue your SAGE journey",
		profile_empty:
			"Create your SAGE profile so the dashboard can recommend the right next step.",
	},
	branch_guidance: {
		title: "Find my best-fit SAGE/SIRT program",
		description:
			"For 12th students choosing a branch with subject strengths, interests, confidence, and expectations.",
		workflow:
			"Turn subjects, interests, confidence, and expectations into SAGE/SIRT program guidance.",
	},
	placement_readiness: {
		title: "Build my placement readiness plan",
		description:
			"For college students connecting skills, projects, resume, training, internships, and career goals.",
	},
	admin_command: {
		title: "Open the command center",
		description:
			"For administrators reviewing readiness, student risk, knowledge quality, and priority actions.",
	},
};

export function normalizeBranding(
	value: Partial<InstitutionBranding> | null | undefined,
): InstitutionBranding {
	return {
		...DEFAULT_BRANDING,
		...(value || {}),
		homepage: {
			...DEFAULT_BRANDING.homepage,
			...(value?.homepage || {}),
		},
		auth: {
			...DEFAULT_BRANDING.auth,
			...(value?.auth || {}),
		},
		branch_guidance: {
			...DEFAULT_BRANDING.branch_guidance,
			...(value?.branch_guidance || {}),
		},
		placement_readiness: {
			...DEFAULT_BRANDING.placement_readiness,
			...(value?.placement_readiness || {}),
		},
		admin_command: {
			...DEFAULT_BRANDING.admin_command,
			...(value?.admin_command || {}),
		},
	};
}
