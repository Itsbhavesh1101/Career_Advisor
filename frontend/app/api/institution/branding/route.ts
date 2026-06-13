import { NextResponse } from "next/server";
import type { InstitutionBranding } from "@/lib/api";
import { DEFAULT_BRANDING, normalizeBranding } from "@/lib/brandingDefaults";

export const dynamic = "force-dynamic";

function resolveBackendBase(): string {
	const configured =
		process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ||
		process.env.API_BASE_URL?.trim();
	return (configured || "http://127.0.0.1:8000").replace(/\/+$/, "");
}

export async function GET() {
	const controller = new AbortController();
	const timeout = setTimeout(() => controller.abort(), 2500);

	try {
		const response = await fetch(
			`${resolveBackendBase()}/api/v1/institution/branding`,
			{
				cache: "no-store",
				signal: controller.signal,
			},
		);
		if (response.ok) {
			const branding = (await response.json()) as InstitutionBranding;
			return NextResponse.json(normalizeBranding(branding), {
				headers: { "Cache-Control": "no-store" },
			});
		}
	} catch {
		// Public pages should stay usable when the local backend is not running.
	} finally {
		clearTimeout(timeout);
	}

	return NextResponse.json(DEFAULT_BRANDING, {
		headers: { "Cache-Control": "no-store" },
	});
}
