"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import ProfileSummaryCard from "@/components/ProfileSummaryCard";
import {
	buttonClass,
	EmptyState,
	Notice,
	PageHeader,
	PageShell,
} from "@/components/ui";
import { listProfiles, type StudentProfileRead } from "@/lib/api";
import { useBranding } from "@/lib/branding";
import {
	clearStoredProfileId,
	clearStoredUserType,
	resolveStoredProfile,
} from "@/lib/profile";

export default function ProfileIndexPage() {
	const router = useRouter();
	const [profile, setProfile] = useState<StudentProfileRead | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const branding = useBranding();

	const handleReset = () => {
		clearStoredProfileId();
		clearStoredUserType();
		router.push("/");
	};

	useEffect(() => {
		let mounted = true;

		async function load() {
			setLoading(true);
			setError(null);
			try {
				const profiles = await listProfiles();
				if (!mounted) return;

				if (profiles.length === 0) {
					router.push("/create-profile");
					return;
				}

				setProfile(resolveStoredProfile(profiles));
			} catch (err) {
				if (mounted) {
					setError(
						err instanceof Error ? err.message : "Failed to load profile.",
					);
				}
			} finally {
				if (mounted) setLoading(false);
			}
		}

		void load();

		return () => {
			mounted = false;
		};
	}, [router]);

	if (loading) {
		return (
			<PageShell className="max-w-4xl">
				<div className="h-28 animate-pulse rounded-xl border border-black/10 bg-white/70" />
			</PageShell>
		);
	}

	if (error) {
		return (
			<PageShell className="max-w-4xl">
				<Notice
					title="Profile could not load"
					description={error}
					tone="danger"
				/>
			</PageShell>
		);
	}

	if (!profile) {
		return (
			<PageShell className="max-w-4xl">
				<EmptyState
					title="No profile found"
					description={
						branding.auth.profile_empty ||
						"Create your SAGE profile so the dashboard can recommend the right next step."
					}
					action={
						<Link
							href="/create-profile"
							className={buttonClass({ variant: "primary" })}
						>
							Create profile
						</Link>
					}
				/>
			</PageShell>
		);
	}

	return (
		<PageShell className="max-w-4xl">
			<PageHeader
				title="Your profile"
				description="Keep the intake data current so recommendations, readiness checks, and evidence stay useful."
			/>
			<ProfileSummaryCard profile={profile} onReset={handleReset} />
		</PageShell>
	);
}
