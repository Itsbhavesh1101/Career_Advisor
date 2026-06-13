import "./globals.css";

import { Manrope, Space_Grotesk } from "next/font/google";
import AppShell from "@/components/AppShell";
import AuthGate from "@/components/AuthGate";

const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope" });
const spaceGrotesk = Space_Grotesk({
	subsets: ["latin"],
	variable: "--font-space-grotesk",
});

export const metadata = {
	title: "SAGE Career Navigator",
	description:
		"Student success, admission guidance, and placement readiness for SAGE/SIRT.",
	icons: {
		icon: "/favicon.svg",
	},
};

export default function RootLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<html lang="en">
			<body
				className={`${manrope.variable} ${spaceGrotesk.variable} min-h-screen overflow-x-hidden bg-white text-[#15110d] antialiased`}
			>
				<AuthGate />
				<AppShell>{children}</AppShell>
			</body>
		</html>
	);
}
