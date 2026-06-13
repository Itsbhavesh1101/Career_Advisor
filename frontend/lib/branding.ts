"use client";

import { useEffect, useState } from "react";
import type { InstitutionBranding } from "@/lib/api";
import { DEFAULT_BRANDING, normalizeBranding } from "@/lib/brandingDefaults";

export { DEFAULT_BRANDING };

export function brandInitials(branding: InstitutionBranding): string {
	if (branding.mode === "sage") return "SG";
	const productName = branding.product_name || DEFAULT_BRANDING.product_name;
	return productName
		.split(/\s+/)
		.filter(Boolean)
		.slice(0, 2)
		.map((word) => word[0]?.toUpperCase())
		.join("");
}

export function useBranding(): InstitutionBranding {
	const [branding, setBranding] =
		useState<InstitutionBranding>(DEFAULT_BRANDING);

	useEffect(() => {
		let active = true;

		async function loadBranding() {
			try {
				const response = await fetch("/api/institution/branding", {
					cache: "no-store",
				});
				if (!response.ok) {
					throw new Error("Branding proxy failed");
				}
				const nextBranding =
					(await response.json()) as Partial<InstitutionBranding>;
				if (!active) return;
				const normalized = normalizeBranding(nextBranding);
				setBranding(normalized);
				document.title = normalized.product_name;
			} catch {
				if (!active) return;
				setBranding(DEFAULT_BRANDING);
				document.title = DEFAULT_BRANDING.product_name;
			}
		}

		void loadBranding();

		return () => {
			active = false;
		};
	}, []);

	return branding;
}
