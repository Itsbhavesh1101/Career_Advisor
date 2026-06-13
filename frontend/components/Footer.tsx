"use client";

import { useBranding } from "@/lib/branding";

export default function Footer() {
	const branding = useBranding();

	return (
		<footer className="border-t border-black/10 bg-white">
			<div className="mx-auto flex max-w-6xl flex-col gap-2 px-5 py-5 text-xs text-zinc-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
				<p className="font-semibold text-zinc-700">{branding.product_name}</p>
				<p className="max-w-2xl sm:text-right">
					2026 launch build, Department of Artificial
					Intelligence and Machine Learning.
				</p>
			</div>
		</footer>
	);
}
