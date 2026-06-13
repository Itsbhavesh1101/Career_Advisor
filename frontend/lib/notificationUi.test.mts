import assert from "node:assert/strict";
import {
	buildNotificationTone,
	summarizeNotification,
} from "./notificationUi.ts";

assert.equal(
	buildNotificationTone({ priority: "high", read_at: null }),
	"orange",
);
assert.equal(
	buildNotificationTone({
		priority: "normal",
		read_at: "2026-05-26T00:00:00Z",
	}),
	"neutral",
);

const summary = summarizeNotification({
	title: "Interview scheduled",
	message: "Round 1 is tomorrow.",
	action_url: "/internship",
});
assert.equal(summary.title, "Interview scheduled");
assert.equal(summary.description, "Round 1 is tomorrow.");
assert.equal(summary.actionLabel, "Open");

console.log("notificationUi tests passed");
