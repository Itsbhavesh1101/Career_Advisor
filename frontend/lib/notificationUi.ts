type NotificationToneInput = {
	priority: string;
	read_at?: string | null;
};

type NotificationSummaryInput = {
	title: string;
	message?: string | null;
	action_url?: string | null;
};

export function buildNotificationTone(input: NotificationToneInput) {
	if (input.read_at) return "neutral";
	return input.priority === "high" ? "orange" : "black";
}

export function summarizeNotification(input: NotificationSummaryInput) {
	return {
		title: input.title,
		description: input.message || "New update available.",
		actionLabel: input.action_url ? "Open" : "Review",
	};
}
