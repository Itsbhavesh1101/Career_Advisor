export interface SupabasePasswordSession {
	access_token: string;
	refresh_token: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === "object" && value !== null;
}

function readTokenPair(value: unknown): SupabasePasswordSession | null {
	if (!isRecord(value)) return null;
	const accessToken = value.access_token;
	const refreshToken = value.refresh_token;
	if (typeof accessToken !== "string" || typeof refreshToken !== "string") {
		return null;
	}
	if (!accessToken.trim() || !refreshToken.trim()) {
		return null;
	}
	return {
		access_token: accessToken,
		refresh_token: refreshToken,
	};
}

export function extractPasswordSession(
	payload: unknown,
): SupabasePasswordSession | null {
	const directSession = readTokenPair(payload);
	if (directSession) return directSession;

	if (!isRecord(payload) || !isRecord(payload.data)) {
		return null;
	}

	return readTokenPair(payload.data.session);
}

export function shouldUsePasswordProxyFallback(error: unknown): boolean {
	if (!error) return false;
	const message = error instanceof Error ? error.message : String(error);
	return /auth session or user missing/i.test(message);
}

export function getPasswordAuthErrorMessage(payload: unknown): string {
	if (!isRecord(payload)) {
		return "Login failed.";
	}

	const error = payload.error;
	if (typeof error === "string" && error.trim()) {
		return error;
	}
	if (isRecord(error) && typeof error.message === "string") {
		return error.message;
	}
	if (typeof payload.error_description === "string") {
		return payload.error_description;
	}
	if (typeof payload.msg === "string") {
		return payload.msg;
	}
	if (typeof payload.message === "string") {
		return payload.message;
	}

	return "Login failed.";
}
