"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import ProfileForm from "@/components/ProfileForm";
import {
	buttonClass,
	GlassPanel,
	PageHeader,
	PageShell,
	StatusBadge,
} from "@/components/ui";
import { listProfiles } from "@/lib/api";
import { getStoredUserType, resolveStoredProfile } from "@/lib/profile";

function CreateProfileContent() {
	const [savedProfileId, setSavedProfileId] = useState<string | null>(null);
	const [preferredFormType, setPreferredFormType] = useState<
		"twelfth" | "college"
	>("college");
	const searchParams = useSearchParams();
	const queryType = searchParams?.get("type");
	let formType: "twelfth" | "college" = preferredFormType;
	if (queryType === "twelfth") formType = "twelfth";
	if (queryType === "college") formType = "college";

	useEffect(() => {
		let mounted = true;
		async function loadSavedProfile() {
			try {
				const profiles = await listProfiles();
				if (!mounted) return;
				const activeProfile = resolveStoredProfile(profiles);
				setSavedProfileId(activeProfile ? activeProfile.id.toString() : null);
			} catch {
				if (mounted) setSavedProfileId(null);
			}
		}

		void loadSavedProfile();

		const storedUserType = getStoredUserType();
		if (storedUserType === "twelfth_student") {
			setPreferredFormType("twelfth");
		}

		return () => {
			mounted = false;
		};
	}, []);

	return (
		<>
			<PageHeader
				title={
					formType === "twelfth"
						? "Build your branch guidance profile"
						: "Build your placement profile"
				}
				description={
					formType === "twelfth"
						? "Share subjects, interests, and decision signals so guidance stays focused on branch and program fit."
						: "Share degree, skills, projects, internships, and placement goals so readiness actions are concrete."
				}
				actions={
					<StatusBadge tone={formType === "twelfth" ? "orange" : "dark"}>
						{formType === "twelfth" ? "12th guidance" : "College readiness"}
					</StatusBadge>
				}
			/>
			{savedProfileId ? (
				<GlassPanel className="mt-5 p-4">
					<div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
						<p className="text-sm text-zinc-600">
							A saved profile is available. Continue the dashboard or create a
							new intake when the student path has changed.
						</p>
						<div className="flex flex-wrap gap-2">
							<Link href="/dashboard" className={buttonClass()}>
								Continue dashboard
							</Link>
							<button
								type="button"
								onClick={() => setSavedProfileId(null)}
								className={buttonClass({ variant: "secondary" })}
							>
								New profile
							</button>
						</div>
					</div>
				</GlassPanel>
			) : null}
			<div className="mt-6">
				<ProfileForm formType={formType} />
			</div>
		</>
	);
}

export default function CreateProfilePage() {
	return (
		<PageShell className="max-w-5xl">
			<Suspense fallback={<div className="text-zinc-700">Loading...</div>}>
				<CreateProfileContent />
			</Suspense>
		</PageShell>
	);
}
