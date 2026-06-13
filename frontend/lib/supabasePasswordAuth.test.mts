import assert from "node:assert/strict";
import test from "node:test";
import {
	extractPasswordSession,
	shouldUsePasswordProxyFallback,
} from "./supabasePasswordAuth.ts";

test("extractPasswordSession reads direct Supabase token responses", () => {
	const session = extractPasswordSession({
		access_token: "access-token",
		refresh_token: "refresh-token",
		user: { id: "user-1" },
	});

	assert.deepEqual(session, {
		access_token: "access-token",
		refresh_token: "refresh-token",
	});
});

test("extractPasswordSession reads nested session responses", () => {
	const session = extractPasswordSession({
		data: {
			session: {
				access_token: "nested-access",
				refresh_token: "nested-refresh",
			},
		},
		user: { id: "user-1" },
	});

	assert.deepEqual(session, {
		access_token: "nested-access",
		refresh_token: "nested-refresh",
	});
});

test("extractPasswordSession rejects null browser auth sessions", () => {
	const session = extractPasswordSession({
		data: { session: null },
		user: null,
	});

	assert.equal(session, null);
});

test("shouldUsePasswordProxyFallback catches browser null-session auth errors", () => {
	assert.equal(
		shouldUsePasswordProxyFallback(new Error("Auth session or user missing")),
		true,
	);
	assert.equal(
		shouldUsePasswordProxyFallback(new Error("Invalid login credentials")),
		false,
	);
	assert.equal(shouldUsePasswordProxyFallback(null), false);
});
