import { NextResponse } from "next/server";
import {
	extractPasswordSession,
	getPasswordAuthErrorMessage,
} from "@/lib/supabasePasswordAuth";

export const runtime = "nodejs";

function readSupabaseConfig(): { anonKey: string; url: string } | null {
	const url = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim();
	const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim();
	if (!url || !anonKey) return null;
	return { anonKey, url: url.replace(/\/+$/, "") };
}

export async function POST(request: Request) {
	const config = readSupabaseConfig();
	if (!config) {
		return NextResponse.json(
			{ error: { message: "Supabase Auth is not configured." } },
			{ status: 500 },
		);
	}

	let body: unknown;
	try {
		body = await request.json();
	} catch {
		return NextResponse.json(
			{ error: { message: "Invalid login payload." } },
			{ status: 400 },
		);
	}

	const email =
		typeof body === "object" && body !== null && "email" in body
			? String(body.email).trim()
			: "";
	const password =
		typeof body === "object" && body !== null && "password" in body
			? String(body.password)
			: "";

	if (!email || !password) {
		return NextResponse.json(
			{ error: { message: "Email and password are required." } },
			{ status: 400 },
		);
	}

	const response = await fetch(
		`${config.url}/auth/v1/token?grant_type=password`,
		{
			method: "POST",
			headers: {
				Authorization: `Bearer ${config.anonKey}`,
				apikey: config.anonKey,
				"Content-Type": "application/json;charset=UTF-8",
				"X-Client-Info": "sage-next-password-auth",
			},
			body: JSON.stringify({
				email,
				password,
				gotrue_meta_security: {},
			}),
		},
	);

	const payload = await response.json().catch(() => null);
	if (!response.ok) {
		return NextResponse.json(
			{ error: { message: getPasswordAuthErrorMessage(payload) } },
			{ status: response.status },
		);
	}

	const session = extractPasswordSession(payload);
	if (!session) {
		return NextResponse.json(
			{ error: { message: "Supabase did not return a login session." } },
			{ status: 502 },
		);
	}

	return NextResponse.json(session);
}
