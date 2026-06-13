"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { buttonClass, FormSection } from "@/components/ui";
import {
	createProfile,
	type StudentProfileCreate,
	type StudentProfileRead,
} from "@/lib/api";
import { setStoredProfileId, setStoredUserType } from "@/lib/profile";

type ProfileFormProps = {
	onCreated?: (profile: StudentProfileRead) => void;
	initialValues?: Partial<StudentProfileCreate>;
	onSubmitOverride?: (
		payload: StudentProfileCreate,
	) => Promise<StudentProfileRead>;
	submitLabel?: string;
	formType?: "twelfth" | "college";
};

const parseCommaList = (value: string): string[] =>
	value
		.split(",")
		.map((item) => item.trim())
		.filter(Boolean);

const labelClass = "flex flex-col gap-2 text-sm font-semibold text-zinc-700";
const inputClass =
	"rounded-lg border border-black/10 bg-white px-3 py-2 text-sm text-zinc-950 placeholder:text-zinc-400 outline-none focus:ring-2 focus:ring-orange-300";
const selectClass =
	"rounded-lg border border-black/10 bg-white px-3 py-2 text-sm text-zinc-950 outline-none focus:ring-2 focus:ring-orange-300";

export default function ProfileForm({
	onCreated,
	initialValues,
	onSubmitOverride,
	submitLabel,
	formType = "college",
}: ProfileFormProps) {
	const router = useRouter();
	const [form, setForm] = useState({
		name: initialValues?.name ?? "",
		twelfth_percentage:
			initialValues?.twelfth_percentage !== undefined
				? String(initialValues.twelfth_percentage)
				: "",
		cgpa: initialValues?.cgpa !== undefined ? String(initialValues.cgpa) : "",
		degree: initialValues?.degree ?? "",
		specialization: initialValues?.specialization ?? "",
		current_skills: initialValues?.current_skills?.join(", ") ?? "",
		interests: initialValues?.interests?.join(", ") ?? "",
		target_industry: initialValues?.target_industry ?? "",
		projects:
			initialValues?.projects !== undefined
				? String(initialValues.projects)
				: "0",
		internships:
			initialValues?.internships !== undefined
				? String(initialValues.internships)
				: "0",
		certifications:
			initialValues?.certifications !== undefined
				? String(initialValues.certifications)
				: "0",
		subjects: initialValues?.subjects?.join(", ") ?? "",
		math_strength: initialValues?.math_strength ?? "",
		logical_reasoning: initialValues?.logical_reasoning ?? "",
		programming_interest: initialValues?.programming_interest ?? "",
	});
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const payload: StudentProfileCreate | null = useMemo(() => {
		const userType =
			formType === "twelfth" ? "twelfth_student" : "college_student";
		const twelfth = form.twelfth_percentage
			? Number(form.twelfth_percentage)
			: null;
		const cgpa = form.cgpa ? Number(form.cgpa) : null;
		const subjects = parseCommaList(form.subjects);
		const interests = parseCommaList(form.interests);
		const currentSkills = parseCommaList(form.current_skills);

		if (!form.name) {
			return null;
		}

		if (userType === "twelfth_student") {
			if (
				twelfth === null ||
				Number.isNaN(twelfth) ||
				interests.length === 0 ||
				subjects.length === 0 ||
				!form.math_strength ||
				!form.logical_reasoning
			) {
				return null;
			}
		} else if (
			cgpa === null ||
			Number.isNaN(cgpa) ||
			!form.degree ||
			!form.specialization ||
			!form.target_industry
		) {
			return null;
		}

		return {
			name: form.name,
			twelfth_percentage: userType === "twelfth_student" ? twelfth : null,
			cgpa: userType === "college_student" ? cgpa : null,
			degree: userType === "college_student" ? form.degree : null,
			specialization:
				userType === "college_student" ? form.specialization : null,
			current_skills: userType === "college_student" ? currentSkills : [],
			interests,
			target_industry: form.target_industry || null,
			projects: Number(form.projects) || 0,
			internships: Number(form.internships) || 0,
			certifications: Number(form.certifications) || 0,
			subjects: userType === "twelfth_student" ? subjects : undefined,
			math_strength:
				userType === "twelfth_student"
					? form.math_strength || undefined
					: undefined,
			logical_reasoning:
				userType === "twelfth_student"
					? form.logical_reasoning || undefined
					: undefined,
			programming_interest:
				userType === "twelfth_student"
					? form.programming_interest || undefined
					: undefined,
			user_type: userType,
		};
	}, [form, formType]);

	async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setError(null);

		if (!payload) {
			setError("Please fill in the required fields.");
			return;
		}

		try {
			setLoading(true);
			const result = onSubmitOverride
				? await onSubmitOverride(payload)
				: await createProfile(payload);
			setStoredProfileId(result.id);
			const userType =
				payload.user_type ||
				(formType === "twelfth" ? "twelfth_student" : "college_student");
			setStoredUserType(userType);
			if (onCreated) {
				onCreated(result);
			} else if (onSubmitOverride) {
				router.push(`/analysis/${result.id}`);
			} else {
				router.push(`/onboarding/quiz/${result.id}`);
			}
		} catch (err) {
			setError(
				err instanceof Error ? err.message : "Failed to create profile.",
			);
		} finally {
			setLoading(false);
		}
	}

	return (
		<form
			onSubmit={handleSubmit}
			className="space-y-5 rounded-xl border border-black/10 bg-white p-5 shadow-[0_8px_26px_rgba(15,23,42,0.05)] sm:p-6"
		>
			<div className="rounded-xl border border-orange-200 bg-orange-50 p-4">
				<p className="text-sm font-semibold text-orange-900">
					{formType === "twelfth"
						? "Branch guidance intake"
						: "Placement readiness intake"}
				</p>
				<p className="mt-1 text-xs leading-5 text-zinc-600">
					{formType === "twelfth"
						? "This form avoids college-placement defaults and focuses on program-fit signals."
						: "This form focuses on evidence that placement teams and companies can act on."}
				</p>
			</div>

			<FormSection
				title="Identity and academic context"
				description="Required fields used to anchor the student readiness loop."
			>
				<div className="grid gap-4 md:grid-cols-2">
					<label className={labelClass}>
						Name
						<input
							className={inputClass}
							value={form.name}
							onChange={(event) =>
								setForm({ ...form, name: event.target.value })
							}
							required
						/>
					</label>
					{formType === "twelfth" ? (
						<label className={labelClass}>
							12th Percentage
							<input
								type="number"
								step="0.1"
								className={inputClass}
								value={form.twelfth_percentage}
								onChange={(event) =>
									setForm({ ...form, twelfth_percentage: event.target.value })
								}
								required
							/>
						</label>
					) : (
						<label className={labelClass}>
							CGPA
							<input
								type="number"
								step="0.1"
								className={inputClass}
								value={form.cgpa}
								onChange={(event) =>
									setForm({ ...form, cgpa: event.target.value })
								}
								required
							/>
						</label>
					)}
					{formType === "college" && (
						<>
							<label className={labelClass}>
								Degree
								<input
									className={inputClass}
									value={form.degree}
									onChange={(event) =>
										setForm({ ...form, degree: event.target.value })
									}
									required
								/>
							</label>
							<label className={labelClass}>
								Specialization
								<input
									className={inputClass}
									value={form.specialization}
									onChange={(event) =>
										setForm({ ...form, specialization: event.target.value })
									}
									required
								/>
							</label>
						</>
					)}
				</div>
			</FormSection>

			{formType === "college" && (
				<FormSection
					title="Placement evidence"
					description="Skills and proof points used for readiness, resume, and training actions."
				>
					<label className={labelClass}>
						Current Skills (comma-separated)
						<input
							className={inputClass}
							value={form.current_skills}
							onChange={(event) =>
								setForm({ ...form, current_skills: event.target.value })
							}
							placeholder="Python, SQL, TensorFlow"
						/>
					</label>
					<div className="grid gap-4 md:grid-cols-3">
						<label className={labelClass}>
							Projects
							<input
								type="number"
								min="0"
								className={inputClass}
								value={form.projects}
								onChange={(event) =>
									setForm({ ...form, projects: event.target.value })
								}
							/>
						</label>
						<label className={labelClass}>
							Internships
							<input
								type="number"
								min="0"
								className={inputClass}
								value={form.internships}
								onChange={(event) =>
									setForm({ ...form, internships: event.target.value })
								}
							/>
						</label>
						<label className={labelClass}>
							Certifications
							<input
								type="number"
								min="0"
								className={inputClass}
								value={form.certifications}
								onChange={(event) =>
									setForm({ ...form, certifications: event.target.value })
								}
							/>
						</label>
					</div>
				</FormSection>
			)}

			{formType === "twelfth" && (
				<FormSection
					title="Branch fit signals"
					description="Subject strengths and interest signals used for program guidance."
				>
					<label className={labelClass}>
						Strong Subjects (comma-separated)
						<input
							className={inputClass}
							value={form.subjects}
							onChange={(event) =>
								setForm({ ...form, subjects: event.target.value })
							}
							placeholder="Mathematics, Physics, Computer Science"
							required
						/>
					</label>
					<div className="grid gap-4 md:grid-cols-3">
						<label className={labelClass}>
							Math Strength
							<select
								className={selectClass}
								value={form.math_strength}
								onChange={(event) =>
									setForm({ ...form, math_strength: event.target.value })
								}
								required
							>
								<option value="">Select</option>
								<option value="emerging">Emerging</option>
								<option value="moderate">Moderate</option>
								<option value="strong">Strong</option>
							</select>
						</label>
						<label className={labelClass}>
							Logical Reasoning
							<select
								className={selectClass}
								value={form.logical_reasoning}
								onChange={(event) =>
									setForm({ ...form, logical_reasoning: event.target.value })
								}
								required
							>
								<option value="">Select</option>
								<option value="emerging">Emerging</option>
								<option value="moderate">Moderate</option>
								<option value="strong">Strong</option>
							</select>
						</label>
						<label className={labelClass}>
							Programming Interest
							<select
								className={selectClass}
								value={form.programming_interest}
								onChange={(event) =>
									setForm({ ...form, programming_interest: event.target.value })
								}
							>
								<option value="">Not sure yet</option>
								<option value="curious">Curious</option>
								<option value="practicing">Practicing</option>
								<option value="confident">Confident</option>
							</select>
						</label>
					</div>
				</FormSection>
			)}

			<FormSection
				title="Goals and expectations"
				description="These fields keep recommendations tied to student intent."
			>
				<div className="grid gap-4 md:grid-cols-2">
					<label className={labelClass}>
						{formType === "twelfth"
							? "Interests and Branch Expectations"
							: "Interests (comma-separated)"}
						<input
							className={inputClass}
							value={form.interests}
							onChange={(event) =>
								setForm({ ...form, interests: event.target.value })
							}
							placeholder={
								formType === "twelfth"
									? "AI, robotics, coding, campus placements, practical labs"
									: "AI, Robotics, HealthTech"
							}
							required={formType === "twelfth"}
						/>
					</label>
					<label className={labelClass}>
						{formType === "twelfth"
							? "Preferred Career Direction"
							: "Target Industry"}
						<input
							className={inputClass}
							value={form.target_industry}
							onChange={(event) =>
								setForm({ ...form, target_industry: event.target.value })
							}
							required={formType === "college"}
						/>
					</label>
				</div>
			</FormSection>

			<div className="flex flex-col gap-3 border-t border-black/10 pt-5 sm:flex-row sm:items-center sm:justify-between">
				<p className="text-xs leading-5 text-zinc-500">
					Required fields are used immediately for quiz and analysis routing.
				</p>
				<button type="submit" disabled={loading} className={buttonClass()}>
					{loading ? "Saving..." : (submitLabel ?? "Create Profile")}
				</button>
			</div>
			{error ? (
				<p className="text-sm font-medium text-red-600">{error}</p>
			) : null}
		</form>
	);
}
