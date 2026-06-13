"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { getMe } from "@/lib/api";
import { clearStoredSessionHint } from "@/lib/profile";

const PUBLIC_PATHS = ["/", "/login", "/signup"];

export default function AuthGate() {
	const router = useRouter();
	const pathname = usePathname();

	useEffect(() => {
		let active = true;

		const isPublic = PUBLIC_PATHS.includes(pathname);
		const isAdminRoute = pathname.startsWith("/admin");

		async function guard() {
			if (isPublic) {
				return;
			}

			try {
				const me = await getMe();
				if (!active) return;

				if (isAdminRoute && me.role !== "admin") {
					router.replace("/");
				}
			} catch {
				if (!active) return;
				clearStoredSessionHint();
				router.replace("/login");
			}
		}

		void guard();

		return () => {
			active = false;
		};
	}, [pathname, router]);

	return null;
}
