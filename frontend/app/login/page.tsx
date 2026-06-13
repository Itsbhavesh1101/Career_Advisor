"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {
	buttonClass,
	GlassPanel,
	PublicWorkShell,
	StatusBadge,
} from "@/components/ui";
import { getMe } from "@/lib/api";
import { useBranding } from "@/lib/branding";
import { setStoredSessionHint, setStoredUserType } from "@/lib/profile";
import {
	isSupabaseAuthConfigured,
	signInWithSupabase,
	signOutSupabase,
} from "@/lib/supabaseAuth";

export default function LoginPage() {
	const router = useRouter();
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [isAdminLogin, setIsAdminLogin] = useState(false);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const branding = useBranding();

	async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setError(null);
		try {
			setLoading(true);
			if (!isSupabaseAuthConfigured()) {
				throw new Error("Supabase Auth is not configured for this deployment.");
			}
			await signInWithSupabase(email, password);
			const me = await getMe();
			setStoredSessionHint();

			if (isAdminLogin) {
				if (me.role !== "admin") {
					await signOutSupabase();
					setError("This account does not have admin access.");
					return;
				}
				router.push("/admin/dashboard");
				return;
			}

			setStoredUserType(me.student_type || "college_student");
			router.push("/dashboard");
		} catch (err) {
			setError(err instanceof Error ? err.message : "Login failed.");
		} finally {
			setLoading(false);
		}
	}

	return (
		<PublicWorkShell
			title={
				isAdminLogin
					? branding.admin_command.title || "Open command center"
					: branding.auth.login_title || "Continue your SAGE journey"
			}
			description="Sign in to resume branch guidance, placement readiness, or institutional operations."
			aside={
				<div className="grid gap-2 text-sm text-zinc-600">
					<div className="flex items-center justify-between gap-3">
						<span>Student workspace</span>
						<StatusBadge tone="orange">Dashboard</StatusBadge>
					</div>
					<div className="flex items-center justify-between gap-3">
						<span>Admin workspace</span>
						<StatusBadge tone="dark">Command center</StatusBadge>
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
							autoComplete="current-password"
							className="rounded-lg border border-black/10 bg-white px-3 py-2 text-sm text-zinc-950 outline-none focus:ring-2 focus:ring-orange-300"
							value={password}
							onChange={(event) => setPassword(event.target.value)}
							required
						/>
					</label>
					<label className="flex items-center gap-2 text-sm font-medium text-zinc-700">
						<input
							type="checkbox"
							checked={isAdminLogin}
							onChange={(event) => setIsAdminLogin(event.target.checked)}
							className="h-4 w-4 rounded border-black/20 text-orange-500"
						/>
						Admin login
					</label>
					<button
						type="submit"
						disabled={loading}
						className={buttonClass({ className: "w-full" })}
					>
						{loading ? "Signing in..." : "Log in"}
					</button>
					{error ? <p className="text-sm text-red-600">{error}</p> : null}
				</form>
				<p className="mt-4 text-center text-sm text-zinc-500">
					Don&apos;t have an account?{" "}
					<Link
						className="font-semibold text-orange-700 hover:underline"
						href="/signup"
					>
						Sign up
					</Link>
				</p>
			</GlassPanel>
		</PublicWorkShell>
	);
}
