"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { buttonClass, cn } from "@/components/ui";
import { brandInitials, useBranding } from "@/lib/branding";
import {
	clearStoredProfileId,
	clearStoredSessionHint,
	clearStoredUserType,
	hasStoredSessionHint,
} from "@/lib/profile";
import { signOutSupabase } from "@/lib/supabaseAuth";

function navLinkClass(active: boolean) {
	return cn(
		"hidden whitespace-nowrap rounded-full px-3 py-1.5 text-sm font-semibold transition sm:inline-flex",
		active
			? "bg-orange-50 text-orange-700"
			: "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-950",
	);
}

export default function Navbar() {
	const pathname = usePathname();
	const router = useRouter();
	const branding = useBranding();
	const initials = brandInitials(branding);
	const [hasSession, setHasSession] = useState(false);

	useEffect(() => {
		setHasSession(hasStoredSessionHint());
		function syncSessionHint() {
			setHasSession(hasStoredSessionHint());
		}

		window.addEventListener("storage", syncSessionHint);
		return () => {
			window.removeEventListener("storage", syncSessionHint);
		};
	}, []);

	async function handleLogout() {
		try {
			await signOutSupabase();
		} finally {
			clearStoredProfileId();
			clearStoredSessionHint();
			clearStoredUserType();
			setHasSession(false);
			router.push("/");
		}
	}

	return (
		<header className="sticky top-0 z-50 w-full overflow-x-hidden border-b border-black/10 bg-white px-3 py-3 sm:px-6">
			<div className="mx-auto flex max-w-6xl items-center justify-between gap-3">
				<Link
					href="/"
					className="flex min-w-0 items-center gap-3 text-base font-bold text-zinc-950 sm:text-lg"
				>
					<span className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-950 text-sm text-white shadow-sm">
						{initials}
					</span>
					<span className="hidden truncate sm:inline">
						{branding.product_name}
					</span>
					<span className="sm:hidden">{initials}</span>
				</Link>
				<nav className="flex min-w-0 shrink-0 items-center justify-end gap-1 text-xs font-medium text-zinc-600 sm:gap-2 sm:text-sm">
					<Link href="/" className={navLinkClass(pathname === "/")}>
						Home
					</Link>
					{hasSession ? (
						<>
							<Link
								href="/dashboard"
								className={navLinkClass(pathname === "/dashboard")}
							>
								Dashboard
							</Link>
							<button
								type="button"
								onClick={handleLogout}
								className={cn(
									buttonClass({ variant: "secondary" }),
									"min-h-9 shrink-0 px-3 py-1 text-xs sm:px-4",
								)}
							>
								Logout
							</button>
						</>
					) : (
						<>
							<Link
								href="/login"
								className={navLinkClass(pathname === "/login")}
							>
								Log In
							</Link>
							<Link
								href="/signup"
								className={cn(
									buttonClass({ variant: "primary" }),
									"min-h-9 shrink-0 px-3 py-1 text-xs sm:px-4",
								)}
							>
								<span className="hidden sm:inline">Sign Up</span>
								<span className="sm:hidden">Join</span>
							</Link>
						</>
					)}
				</nav>
			</div>
		</header>
	);
}
