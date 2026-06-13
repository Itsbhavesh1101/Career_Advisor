"use client";

import {
	Bell,
	BookOpenCheck,
	BriefcaseBusiness,
	CheckCheck,
	FileText,
	GraduationCap,
	LayoutDashboard,
	LogOut,
	Menu,
	UserRound,
	X,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import FloatingAssistantBot from "@/components/FloatingAssistantBot";
import Footer from "@/components/Footer";
import Navbar from "@/components/Navbar";
import { buttonClass, cn } from "@/components/ui";
import {
	getMe,
	listNotifications,
	markAllNotificationsRead,
	markNotificationRead,
	type NotificationRead,
} from "@/lib/api";
import { brandInitials, useBranding } from "@/lib/branding";
import {
	buildNotificationTone,
	summarizeNotification,
} from "@/lib/notificationUi";
import {
	clearStoredProfileId,
	clearStoredSessionHint,
	clearStoredUserType,
	getStoredProfileId,
	getStoredUserType,
} from "@/lib/profile";
import { signOutSupabase } from "@/lib/supabaseAuth";

type ShellUser = {
	role: string;
	student_type?: string | null;
} | null;

type NavItem = {
	label: string;
	href: string;
	icon: typeof LayoutDashboard;
};

const PUBLIC_PATHS = ["/", "/login", "/signup"];

function isPublicPath(pathname: string) {
	return PUBLIC_PATHS.includes(pathname);
}

function isActive(pathname: string, href: string, hash: string) {
	if (href.includes("#")) {
		const [basePath, targetHash] = href.split("#");
		return pathname === basePath && hash === `#${targetHash}`;
	}
	if (href === "/dashboard") return pathname === "/dashboard";
	if (href === "/admin/dashboard") {
		return pathname.startsWith("/admin") && !hash;
	}
	return pathname === href || pathname.startsWith(`${href}/`);
}

function profileIdFromPathname(pathname: string): number | null {
	const patterns = [
		/^\/analysis\/(\d+)/,
		/^\/profile\/(\d+)/,
		/^\/profiles\/(\d+)\/edit/,
		/^\/onboarding\/quiz\/(\d+)/,
	];
	for (const pattern of patterns) {
		const match = pathname.match(pattern);
		if (!match?.[1]) continue;
		const value = Number(match[1]);
		if (Number.isFinite(value)) return value;
	}
	return null;
}

function buildNavItems({
	pathname,
	user,
	storedUserType,
	storedProfileId,
}: {
	pathname: string;
	user: ShellUser;
	storedUserType: string | null;
	storedProfileId: string | null;
}): NavItem[] {
	const isAdmin = user?.role === "admin" || pathname.startsWith("/admin");
	if (isAdmin) {
		return [
			{
				label: "Command center",
				href: "/admin/dashboard",
				icon: LayoutDashboard,
			},
		];
	}

	const studentType = user?.student_type || storedUserType;
	const isTwelfth = studentType === "twelfth_student";
	const analysisHref = storedProfileId
		? `/analysis/${storedProfileId}`
		: "/dashboard";
	const items: NavItem[] = [
		{
			label: isTwelfth ? "Guidance hub" : "Readiness hub",
			href: "/dashboard",
			icon: LayoutDashboard,
		},
		{ label: "Profile", href: "/profile", icon: UserRound },
		{
			label: isTwelfth ? "Program guidance" : "Career analysis",
			href: analysisHref,
			icon: GraduationCap,
		},
	];

	if (!isTwelfth) {
		items.push(
			{ label: "Resume", href: "/resume", icon: FileText },
			{ label: "Training", href: "/training", icon: BookOpenCheck },
			{ label: "Internship", href: "/internship", icon: BriefcaseBusiness },
		);
	}

	return items;
}

export default function AppShell({ children }: { children: React.ReactNode }) {
	const pathname = usePathname();
	const router = useRouter();
	const [user, setUser] = useState<ShellUser>(null);
	const [storedProfileId, setStoredProfileId] = useState<string | null>(null);
	const [storedUserType, setStoredUserType] = useState<string | null>(null);
	const [menuOpen, setMenuOpen] = useState(false);
	const [notificationsOpen, setNotificationsOpen] = useState(false);
	const [notifications, setNotifications] = useState<NotificationRead[]>([]);
	const [unreadCount, setUnreadCount] = useState(0);
	const [currentHash, setCurrentHash] = useState("");
	const branding = useBranding();
	const initials = brandInitials(branding);

	useEffect(() => {
		let active = true;
		setMenuOpen(false);
		setNotificationsOpen(false);
		setCurrentHash(window.location.hash);
		setStoredProfileId(getStoredProfileId());
		setStoredUserType(getStoredUserType());

		function syncHash() {
			setCurrentHash(window.location.hash);
		}
		window.addEventListener("hashchange", syncHash);

		async function loadSession() {
			if (isPublicPath(pathname)) {
				setUser(null);
				return;
			}
			try {
				const me = await getMe();
				if (!active) return;
				setUser(me);
				try {
					const notificationData = await listNotifications({ limit: 6 });
					if (!active) return;
					setNotifications(notificationData.items);
					setUnreadCount(notificationData.unread_count);
				} catch {
					if (!active) return;
					setNotifications([]);
					setUnreadCount(0);
				}
			} catch {
				if (!active) return;
				setUser(null);
				setNotifications([]);
				setUnreadCount(0);
			}
		}

		void loadSession();
		return () => {
			active = false;
			window.removeEventListener("hashchange", syncHash);
		};
	}, [pathname]);

	const publicRoute = isPublicPath(pathname);
	const navItems = useMemo(
		() =>
			buildNavItems({
				pathname,
				user,
				storedUserType,
				storedProfileId,
			}),
		[pathname, user, storedUserType, storedProfileId],
	);
	const isAdmin = user?.role === "admin" || pathname.startsWith("/admin");
	const storedProfileIdNumber = storedProfileId
		? Number(storedProfileId)
		: null;
	const assistantProfileId =
		storedProfileIdNumber && Number.isFinite(storedProfileIdNumber)
			? storedProfileIdNumber
			: profileIdFromPathname(pathname);
	const assistantStudentType = user?.student_type || storedUserType;
	const shellTitle = isAdmin
		? "Admin command"
		: storedUserType === "twelfth_student" ||
				user?.student_type === "twelfth_student"
			? "Branch guidance"
			: "Placement readiness";

	async function handleLogout() {
		try {
			await signOutSupabase();
		} catch {
			// Clear local navigation state even if the network request fails.
		}
		clearStoredProfileId();
		clearStoredSessionHint();
		clearStoredUserType();
		setUser(null);
		router.push("/login");
	}

	async function refreshNotifications() {
		try {
			const notificationData = await listNotifications({ limit: 6 });
			setNotifications(notificationData.items);
			setUnreadCount(notificationData.unread_count);
		} catch {
			setNotifications([]);
			setUnreadCount(0);
		}
	}

	async function openNotification(notification: NotificationRead) {
		try {
			if (!notification.read_at) {
				await markNotificationRead(notification.id);
				await refreshNotifications();
			}
		} catch {
			// Navigation remains useful even if read state update fails.
		}
		setNotificationsOpen(false);
		if (notification.action_url) {
			router.push(notification.action_url);
		}
	}

	async function markAllRead() {
		try {
			await markAllNotificationsRead();
			await refreshNotifications();
		} catch {
			// Keep the notification menu usable if the update request fails.
		}
	}

	if (publicRoute) {
		return (
			<>
				<Navbar />
				<div className="relative border-t border-black/5 bg-white">
					{children}
					<Footer />
				</div>
			</>
		);
	}

	const navList = (
		<nav className="space-y-1">
			{navItems.map((item) => {
				const Icon = item.icon;
				const active = isActive(pathname, item.href, currentHash);
				return (
					<Link
						key={`${item.label}-${item.href}`}
						href={item.href}
						className={cn(
							"flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-semibold transition",
							active
								? "bg-zinc-950 text-white"
								: "text-zinc-600 hover:bg-orange-50 hover:text-zinc-950",
						)}
					>
						<Icon className="h-4 w-4" />
						<span>{item.label}</span>
					</Link>
				);
			})}
		</nav>
	);

	return (
		<div className="min-h-screen bg-zinc-50 text-zinc-950">
			<aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-black/10 bg-white px-4 py-4 lg:block">
				<Link href="/" className="flex items-center gap-3 font-bold">
					<span className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-950 text-sm text-white">
						{initials}
					</span>
					<span>{branding.product_name}</span>
				</Link>
				<div className="mt-5 rounded-lg border border-black/10 bg-zinc-50 p-3">
					<p className="text-xs font-semibold text-orange-700">{shellTitle}</p>
					<p className="mt-1 text-xs leading-5 text-zinc-500">
						{isAdmin
							? "Operational readiness workspace"
							: "Next actions, evidence, and readiness tools"}
					</p>
				</div>
				<div className="mt-5">{navList}</div>
				<button
					type="button"
					onClick={handleLogout}
					className="absolute right-4 bottom-4 left-4 flex items-center justify-center gap-2 rounded-lg border border-black/10 px-3 py-2 text-sm font-semibold text-zinc-700 transition hover:border-orange-300 hover:bg-orange-50"
				>
					<LogOut className="h-4 w-4" />
					Logout
				</button>
			</aside>

			<div className="lg:pl-64">
				<header className="sticky top-0 z-30 border-b border-black/10 bg-white/95 px-4 py-3 backdrop-blur lg:px-6">
					<div className="flex items-center justify-between gap-3">
						<div>
							<p className="text-sm font-semibold text-zinc-950">
								{shellTitle}
							</p>
							<p className="hidden text-xs text-zinc-500 sm:block">
								{branding.product_name}
							</p>
						</div>
						<div className="flex items-center gap-2">
							<Link
								href="/"
								className={buttonClass({
									variant: "secondary",
									className: "hidden min-h-8 px-3 py-1 text-xs sm:inline-flex",
								})}
							>
								Home
							</Link>
							<div className="relative">
								<button
									type="button"
									onClick={() => setNotificationsOpen((value) => !value)}
									className="relative inline-flex h-9 items-center justify-center gap-2 rounded-lg border border-black/10 bg-white px-3 text-sm font-semibold text-zinc-800 transition hover:border-orange-300 hover:bg-orange-50"
									aria-label="Open notifications"
								>
									<Bell className="h-4 w-4" />
									<span className="hidden sm:inline">Updates</span>
									{unreadCount ? (
										<span className="-top-2 -right-2 absolute flex h-5 min-w-5 items-center justify-center rounded-full bg-orange-600 px-1 text-[11px] text-white">
											{unreadCount > 9 ? "9+" : unreadCount}
										</span>
									) : null}
								</button>
								{notificationsOpen ? (
									<div className="absolute right-0 z-50 mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-black/10 bg-white p-3 shadow-xl">
										<div className="flex items-center justify-between gap-3">
											<p className="font-semibold text-sm text-zinc-950">
												Notifications
											</p>
											<button
												type="button"
												onClick={() => void markAllRead()}
												className="inline-flex items-center gap-1 text-xs font-semibold text-orange-700 hover:text-orange-800"
											>
												<CheckCheck className="h-3.5 w-3.5" />
												Mark read
											</button>
										</div>
										<div className="mt-3 space-y-2">
											{notifications.length ? (
												notifications.map((notification) => {
													const summary = summarizeNotification(notification);
													const tone = buildNotificationTone(notification);
													return (
														<button
															type="button"
															key={notification.id}
															onClick={() =>
																void openNotification(notification)
															}
															className={cn(
																"w-full rounded-lg border p-3 text-left transition",
																tone === "orange"
																	? "border-orange-200 bg-orange-50"
																	: tone === "black"
																		? "border-zinc-200 bg-zinc-50"
																		: "border-black/10 bg-white",
															)}
														>
															<div className="flex items-start justify-between gap-3">
																<p className="font-semibold text-sm text-zinc-950">
																	{summary.title}
																</p>
																<span className="shrink-0 text-[11px] font-semibold text-orange-700">
																	{summary.actionLabel}
																</span>
															</div>
															<p className="mt-1 line-clamp-2 text-xs leading-5 text-zinc-600">
																{summary.description}
															</p>
														</button>
													);
												})
											) : (
												<p className="rounded-lg border border-black/10 bg-zinc-50 p-3 text-sm text-zinc-600">
													No unread updates yet.
												</p>
											)}
										</div>
									</div>
								) : null}
							</div>
							<button
								type="button"
								onClick={() => setMenuOpen(true)}
								className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-black/10 bg-white text-zinc-950 lg:hidden"
								aria-label="Open navigation"
							>
								<Menu className="h-4 w-4" />
							</button>
						</div>
					</div>
				</header>
				<div className="min-h-[calc(100vh-4rem)]">{children}</div>
			</div>

			{user && !isAdmin && assistantProfileId ? (
				<FloatingAssistantBot
					profileId={assistantProfileId}
					studentType={assistantStudentType}
				/>
			) : null}

			{menuOpen ? (
				<div className="fixed inset-0 z-50 lg:hidden">
					<button
						type="button"
						className="absolute inset-0 bg-black/30"
						aria-label="Close navigation"
						onClick={() => setMenuOpen(false)}
					/>
					<div className="absolute top-0 right-0 h-full w-80 max-w-[86vw] border-l border-black/10 bg-white p-4 shadow-xl">
						<div className="flex items-center justify-between">
							<p className="font-semibold text-zinc-950">Workspace</p>
							<button
								type="button"
								onClick={() => setMenuOpen(false)}
								className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-black/10"
								aria-label="Close navigation"
							>
								<X className="h-4 w-4" />
							</button>
						</div>
						<div className="mt-5">{navList}</div>
						<button
							type="button"
							onClick={handleLogout}
							className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg border border-black/10 px-3 py-2 text-sm font-semibold text-zinc-700"
						>
							<LogOut className="h-4 w-4" />
							Logout
						</button>
					</div>
				</div>
			) : null}
		</div>
	);
}
