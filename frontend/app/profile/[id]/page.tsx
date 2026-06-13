"use client";

import { use, useEffect, useState } from "react";

import ProfileSummaryCard from "@/components/ProfileSummaryCard";
import { Notice, PageHeader, PageShell } from "@/components/ui";
import { getProfile, type StudentProfileRead } from "@/lib/api";

type ProfilePageProps = {
	params: Promise<{ id: string }>;
};

export default function ProfilePage({ params }: ProfilePageProps) {
	const { id } = use(params);
	const profileId = Number(id);
	const [profile, setProfile] = useState<StudentProfileRead | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		let mounted = true;

		async function load() {
			try {
				const data = await getProfile(profileId);
				if (mounted) setProfile(data);
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

		if (!Number.isNaN(profileId)) {
			void load();
		} else {
			setError("Invalid profile ID.");
			setLoading(false);
		}

		return () => {
			mounted = false;
		};
	}, [profileId]);

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
				<Notice
					title="Profile not found"
					description="Choose an available profile or create a new intake."
					tone="warning"
				/>
			</PageShell>
		);
	}

	return (
		<PageShell className="max-w-4xl">
			<PageHeader
				title="Profile details"
				description="Review the intake record that drives dashboard next actions and analysis recommendations."
			/>
			<ProfileSummaryCard profile={profile} showSwitch />
		</PageShell>
	);
}
