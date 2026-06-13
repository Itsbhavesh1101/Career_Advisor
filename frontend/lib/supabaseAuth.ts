"use client";

import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import type { StudentType } from "@/lib/api";
import {
	extractPasswordSession,
	getPasswordAuthErrorMessage,
	shouldUsePasswordProxyFallback,
} from "@/lib/supabasePasswordAuth";

let client: SupabaseClient | null = null;

export function isSupabaseAuthConfigured(): boolean {
	return Boolean(
		process.env.NEXT_PUBLIC_SUPABASE_URL?.trim() &&
			process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim(),
	);
}

export function getSupabaseClient(): SupabaseClient | null {
	const url = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim();
	const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim();
	if (!url || !anonKey) return null;
	if (!client) {
		client = createClient(url, anonKey, {
			auth: {
				autoRefreshToken: true,
				persistSession: true,
				detectSessionInUrl: true,
			},
		});
	}
	return client;
}

export async function getSupabaseAccessToken(): Promise<string | null> {
	const supabase = getSupabaseClient();
	if (!supabase) return null;
	const { data, error } = await supabase.auth.getSession();
	if (error) return null;
	return data.session?.access_token ?? null;
}

export async function signInWithSupabase(
	email: string,
	password: string,
): Promise<void> {
	const supabase = getSupabaseClient();
	if (!supabase) throw new Error("Supabase Auth is not configured.");
	const { data, error } = await supabase.auth.signInWithPassword({
		email,
		password,
	});
	if (error && !shouldUsePasswordProxyFallback(error)) {
		throw new Error(error.message);
	}
	if (data.session?.access_token && data.session.refresh_token) {
		return;
	}

	const response = await fetch("/api/auth/password", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({ email, password }),
	});
	const payload = await response.json().catch(() => null);
	if (!response.ok) {
		throw new Error(getPasswordAuthErrorMessage(payload));
	}
	const session = extractPasswordSession(payload);
	if (!session) {
		throw new Error("Supabase did not return a login session.");
	}
	const { error: setSessionError } = await supabase.auth.setSession(session);
	if (setSessionError) throw new Error(setSessionError.message);
}

export async function signUpWithSupabase(
	email: string,
	password: string,
	studentType: StudentType,
): Promise<void> {
	const supabase = getSupabaseClient();
	if (!supabase) throw new Error("Supabase Auth is not configured.");
	const { data, error } = await supabase.auth.signUp({
		email,
		password,
		options: {
			data: {
				student_type: studentType,
			},
		},
	});
	if (error) throw new Error(error.message);
	if (!data.session) {
		await signInWithSupabase(email, password);
	}
}

export async function signOutSupabase(): Promise<void> {
	const supabase = getSupabaseClient();
	if (!supabase) return;
	const { error } = await supabase.auth.signOut();
	if (error) throw new Error(error.message);
}
