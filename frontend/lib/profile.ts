import type { StudentProfileRead, StudentType } from "@/lib/api";

const SESSION_HINT_KEY = "career_session_hint";

export function hasStoredSessionHint(): boolean {
	if (typeof window === "undefined") return false;
	return localStorage.getItem(SESSION_HINT_KEY) === "1";
}

export function setStoredSessionHint() {
	localStorage.setItem(SESSION_HINT_KEY, "1");
}

export function clearStoredSessionHint() {
	localStorage.removeItem(SESSION_HINT_KEY);
}

export function getStoredProfileId(): string | null {
	if (typeof window === "undefined") return null;
	return localStorage.getItem("career_profile_id");
}

export function setStoredProfileId(id: number) {
	localStorage.setItem("career_profile_id", id.toString());
}

export function clearStoredProfileId() {
	localStorage.removeItem("career_profile_id");
}

export function getStoredUserType(): string | null {
	if (typeof window === "undefined") return null;
	return localStorage.getItem("career_user_type");
}

export function setStoredUserType(type: string) {
	localStorage.setItem("career_user_type", type);
}

export function clearStoredUserType() {
	localStorage.removeItem("career_user_type");
}

export function getProfileStudentType(
	profile: StudentProfileRead,
): StudentType {
	return profile.user_type === "twelfth_student" ||
		(!profile.user_type && !profile.degree)
		? "twelfth_student"
		: "college_student";
}

export function getProfileFormType(
	profile: StudentProfileRead,
): "twelfth" | "college" {
	return getProfileStudentType(profile) === "twelfth_student"
		? "twelfth"
		: "college";
}

export function getCreateProfileType(
	type: string | null,
): "twelfth" | "college" {
	return type === "twelfth_student" ? "twelfth" : "college";
}

export function chooseLatestProfile(
	profiles: StudentProfileRead[],
): StudentProfileRead | null {
	if (profiles.length === 0) return null;

	return profiles.reduce((latest, current) => {
		const latestDate = new Date(latest.created_at).getTime();
		const currentDate = new Date(current.created_at).getTime();
		return currentDate > latestDate ? current : latest;
	});
}

export function resolveStoredProfile(
	profiles: StudentProfileRead[],
): StudentProfileRead | null {
	const storedId = getStoredProfileId();
	const validStored = storedId
		? profiles.find((profile) => profile.id === Number(storedId))
		: null;

	if (validStored) {
		setStoredProfileId(validStored.id);
		setStoredUserType(getProfileStudentType(validStored));
		return validStored;
	}

	if (storedId) {
		clearStoredProfileId();
	}

	const latest = chooseLatestProfile(profiles);
	if (latest) {
		setStoredProfileId(latest.id);
		setStoredUserType(getProfileStudentType(latest));
	}

	return latest;
}
