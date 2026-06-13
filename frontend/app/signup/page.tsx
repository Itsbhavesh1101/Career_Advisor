"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
	buttonClass,
	cn,
	GlassPanel,
	PublicWorkShell,
	StatusBadge,
} from "@/components/ui";
import { getMe, type StudentType } from "@/lib/api";
import { useBranding } from "@/lib/branding";
import { setStoredSessionHint, setStoredUserType } from "@/lib/profile";
import {
	isSupabaseAuthConfigured,
	signUpWithSupabase,
} from "@/lib/supabaseAuth";

export default function SignupPage() {
	const router = useRouter();
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [studentType, setStudentType] = useState<StudentType | "">("");
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const branding = useBranding();

	useEffect(() => {
		const requestedType = new URLSearchParams(window.location.search).get(
			"type",
		);
		if (
			requestedType === "twelfth_student" ||
			requestedType === "college_student"
		) {
			setStudentType(requestedType);
		}
	}, []);

	async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setError(null);
		if (!studentType) {
			setError("Select your student path before creating an account.");
			return;
		}

		try {
			setLoading(true);
			if (!isSupabaseAuthConfigured()) {
				throw new Error("Supabase Auth is not configured for this deployment.");
			}
			await signUpWithSupabase(email, password, studentType);
			const me = await getMe();
			setStoredUserType(me.student_type || studentType);
			setStoredSessionHint();
			router.push("/dashboard");
		} catch (err) {
			setError(err instanceof Error ? err.message : "Signup failed.");
		} finally {
			setLoading(false);
		}
	}

	return (
		<PublicWorkShell
			title={branding.auth.signup_title || "Create your SAGE workspace"}
			description="Choose the path that matches your current goal. The dashboard and next actions adapt from this choice."
			aside={
				<div className="grid gap-2 text-sm text-zinc-600">
					<div className="flex items-center justify-between gap-3">
						<span>12th student</span>
						<StatusBadge tone="orange">Branch fit</StatusBadge>
					</div>
					<div className="flex items-center justify-between gap-3">
						<span>College student</span>
						<StatusBadge tone="dark">Placement plan</StatusBadge>
					</div>
				</div>
			}
		>
			<GlassPanel className="p-6">
				<form onSubmit={handleSubmit} className="space-y-4">
					<label className="flex flex-col gap-2 text-sm font-semibold text-zinc-700">
						Email
						<input
							type="email"
							autoComplete="email"
							className="rounded-lg border border-black/10 bg-white px-3 py-2 text-sm text-zinc-950 outline-none focus:ring-2 focus:ring-orange-300"
							value={email}
							onChange={(event) => setEmail(event.target.value)}
							required
						/>
					</label>
					<label className="flex flex-col gap-2 text-sm font-semibold text-zinc-700">
						Password
						<input
							type="password"
							autoComplete="new-password"
							className="rounded-lg border border-black/10 bg-white px-3 py-2 text-sm text-zinc-950 outline-none focus:ring-2 focus:ring-orange-300"
							value={password}
							onChange={(event) => setPassword(event.target.value)}
							required
						/>
					</label>
					<div className="grid gap-3 sm:grid-cols-2">
						<PathButton
							active={studentType === "twelfth_student"}
							title="12th student"
							description="Branch and program guidance"
							onClick={() => setStudentType("twelfth_student")}
						/>
						<PathButton
							active={studentType === "college_student"}
							title="College student"
							description="Placement readiness plan"
							onClick={() => setStudentType("college_student")}
						/>
					</div>
					<button
						type="submit"
						disabled={loading}
						className={buttonClass({ className: "w-full" })}
					>
						{loading ? "Creating account..." : "Create account"}
					</button>
					{error ? <p className="text-sm text-red-600">{error}</p> : null}
				</form>
			</GlassPanel>
		</PublicWorkShell>
	);
}

function PathButton({
	active,
	title,
	description,
	onClick,
}: {
	active: boolean;
	title: string;
	description: string;
	onClick: () => void;
}) {
	return (
		<button
			type="button"
			onClick={onClick}
			className={cn(
				"rounded-xl border p-4 text-left transition",
				active
					? "border-orange-300 bg-orange-50 text-zinc-950"
					: "border-black/10 bg-white/60 text-zinc-700 hover:border-orange-200",
			)}
		>
			<p className="font-semibold">{title}</p>
			<p className="mt-1 text-sm text-zinc-500">{description}</p>
		</button>
	);
}
