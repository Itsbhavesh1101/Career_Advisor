"use client";

import {
	BotMessageSquare,
	Loader2,
	MessageCircle,
	Send,
	Sparkles,
	X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { buttonClass, cn, fieldControlClass } from "@/components/ui";
import { LONG_WAIT_NOTICE, toGentleAiMessage } from "@/lib/aiUx";
import { sendChatMessage } from "@/lib/api";
import { useDelayedFlag } from "@/lib/useDelayedFlag";

type AssistantMessage = {
	role: "user" | "assistant";
	content: string;
};

type FloatingAssistantBotProps = {
	profileId: number;
	studentType: string | null;
};

function isTwelfthStudent(studentType: string | null) {
	return studentType === "twelfth_student";
}

function DoodleAvatar({ active }: { active: boolean }) {
	return (
		<div className="relative flex h-12 w-12 items-center justify-center">
			<span className="assistant-doodle-signal absolute h-12 w-12 rounded-full border border-orange-300" />
			<span className="assistant-doodle-signal absolute h-10 w-10 rounded-full border border-orange-200 [animation-delay:0.55s]" />
			<svg
				viewBox="0 0 64 64"
				aria-hidden="true"
				className="assistant-doodle relative h-12 w-12 drop-shadow-[0_10px_18px_rgba(249,115,22,0.18)]"
			>
				<path
					d="M17 30c0-11 7-18 18-18s18 7 18 18v9c0 7-5 12-12 12H27c-6 0-10-4-10-10V30Z"
					fill={active ? "#f97316" : "#15110d"}
				/>
				<path
					d="M20 42c-5 0-8-3-8-8 0-4 2-7 6-8M51 26c4 1 7 4 7 8 0 5-3 8-8 8"
					fill="none"
					stroke="#15110d"
					strokeLinecap="round"
					strokeWidth="3"
				/>
				<circle
					cx="27"
					cy="33"
					r="3"
					fill="white"
					className="assistant-doodle-eye"
				/>
				<circle
					cx="42"
					cy="33"
					r="3"
					fill="white"
					className="assistant-doodle-eye"
				/>
				<path
					d="M28 43c4 3 10 3 14 0"
					fill="none"
					stroke="white"
					strokeLinecap="round"
					strokeWidth="3"
				/>
				<path
					d="M35 12V7"
					fill="none"
					stroke="#15110d"
					strokeLinecap="round"
					strokeWidth="3"
				/>
				<circle
					cx="35"
					cy="5"
					r="3"
					fill="#f97316"
					stroke="#15110d"
					strokeWidth="2"
				/>
			</svg>
		</div>
	);
}

export default function FloatingAssistantBot({
	profileId,
	studentType,
}: FloatingAssistantBotProps) {
	const [open, setOpen] = useState(false);
	const [input, setInput] = useState("");
	const [messages, setMessages] = useState<AssistantMessage[]>([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const scrollRef = useRef<HTMLDivElement | null>(null);
	const showLongWaitHint = useDelayedFlag(loading, 7000);
	const twelfth = isTwelfthStudent(studentType);

	const persona = useMemo(
		() =>
			twelfth
				? {
						title: "Counselor bot",
						label: "Branch guidance",
						description:
							"Ask about program fit, expectation checks, and what to discuss next.",
						placeholder: "Ask about branch fit or next counseling step...",
						greeting:
							"I can help you understand branch fit, expectation reality checks, and the next action before counseling.",
						prompts: [
							"Which program fit should I discuss first?",
							"Explain my expectation reality check.",
							"What should I do this week?",
						],
					}
				: {
						title: "Assistant copilot",
						label: "Placement readiness",
						description:
							"Ask about resume proof, role gaps, training, internships, and next actions.",
						placeholder: "Ask about resume, roles, or readiness...",
						greeting:
							"I can help you turn your analysis into resume, project, training, and placement actions.",
						prompts: [
							"What is my next placement action?",
							"Which resume proof should I improve?",
							"What role should I target first?",
						],
					},
		[twelfth],
	);

	useEffect(() => {
		if (!messages.length) {
			setMessages([{ role: "assistant", content: persona.greeting }]);
		}
	}, [messages.length, persona.greeting]);

	useEffect(() => {
		if (scrollRef.current) {
			scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
		}
	});

	async function sendMessage(content: string) {
		const trimmed = content.trim();
		if (!trimmed || loading) return;
		setInput("");
		setError(null);
		setMessages((current) => [...current, { role: "user", content: trimmed }]);
		try {
			setLoading(true);
			const response = await sendChatMessage(profileId, trimmed);
			setMessages((current) => [
				...current,
				{ role: "assistant", content: response.response },
			]);
		} catch (err) {
			const rawMessage =
				err instanceof Error ? err.message : "Chat request failed.";
			const message = rawMessage.toLowerCase().includes("analysis")
				? "Run or refresh your analysis first, then I can give profile-aware advice."
				: toGentleAiMessage(rawMessage);
			setError(message);
		} finally {
			setLoading(false);
		}
	}

	return (
		<div className="fixed right-4 bottom-4 z-50 sm:right-5 sm:bottom-5">
			{open ? (
				<section className="mb-3 w-[min(24rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-black/10 bg-white/95 shadow-[0_24px_70px_rgba(15,23,42,0.22)] backdrop-blur-xl">
					<header className="flex items-center justify-between gap-3 border-black/10 border-b bg-zinc-950 p-4 text-white">
						<div className="flex items-center gap-3">
							<DoodleAvatar active />
							<div>
								<p className="flex items-center gap-2 font-semibold text-sm">
									{persona.title}
									<Sparkles className="h-3.5 w-3.5 text-orange-300" />
								</p>
								<p className="text-xs text-zinc-300">{persona.label}</p>
							</div>
						</div>
						<button
							type="button"
							onClick={() => setOpen(false)}
							className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/15 bg-white/10 text-white transition hover:bg-white/20"
							aria-label="Close assistant"
						>
							<X className="h-4 w-4" />
						</button>
					</header>

					<div className="p-4">
						<p className="text-sm leading-5 text-zinc-600">
							{persona.description}
						</p>
						<div className="mt-3 flex flex-wrap gap-2">
							{persona.prompts.map((prompt) => (
								<button
									type="button"
									key={prompt}
									onClick={() => void sendMessage(prompt)}
									disabled={loading}
									className="rounded-full border border-orange-200 bg-orange-50 px-3 py-1.5 text-left text-xs font-semibold text-orange-800 transition hover:border-orange-300 hover:bg-orange-100 disabled:opacity-60"
								>
									{prompt}
								</button>
							))}
						</div>

						<div
							ref={scrollRef}
							className="mt-4 h-72 space-y-3 overflow-y-auto rounded-xl border border-black/10 bg-zinc-50 p-3"
							aria-live="polite"
						>
							{messages.map((message, index) => (
								<div
									key={`${message.role}-${index}`}
									className={cn(
										"max-w-[88%] whitespace-pre-wrap break-words rounded-xl px-3 py-2 text-sm leading-5",
										message.role === "user"
											? "ml-auto bg-orange-500 text-white"
											: "border border-black/10 bg-white text-zinc-700",
									)}
								>
									{message.content}
								</div>
							))}
							{loading ? (
								<div className="flex items-center gap-2 text-xs text-zinc-500">
									<Loader2 className="h-3.5 w-3.5 animate-spin" />
									Thinking through your profile...
								</div>
							) : null}
							{loading && showLongWaitHint ? (
								<p className="text-xs text-zinc-500">{LONG_WAIT_NOTICE}</p>
							) : null}
						</div>

						{error ? (
							<p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
								{error}
							</p>
						) : null}

						<form
							className="mt-4 flex gap-2"
							onSubmit={(event) => {
								event.preventDefault();
								void sendMessage(input);
							}}
						>
							<input
								value={input}
								onChange={(event) => setInput(event.target.value)}
								placeholder={persona.placeholder}
								className={`${fieldControlClass} rounded-full`}
							/>
							<button
								type="submit"
								disabled={loading || !input.trim()}
								className={buttonClass({
									className: "h-11 w-11 shrink-0 px-0",
								})}
								aria-label="Send message"
							>
								<Send className="h-4 w-4" />
							</button>
						</form>
					</div>
				</section>
			) : null}

			<button
				type="button"
				onClick={() => setOpen((value) => !value)}
				className="group flex items-center gap-3 rounded-full border border-black/10 bg-white/95 p-2 pr-4 text-left shadow-[0_16px_48px_rgba(15,23,42,0.18)] backdrop-blur-xl transition hover:-translate-y-0.5 hover:border-orange-300"
				aria-expanded={open}
				aria-label={`Open ${persona.title}`}
			>
				<DoodleAvatar active={open} />
				<span className="hidden sm:block">
					<span className="block text-sm font-semibold text-zinc-950">
						{persona.title}
					</span>
					<span className="block text-xs text-zinc-500">{persona.label}</span>
				</span>
				<MessageCircle className="h-4 w-4 text-orange-600 sm:hidden" />
				<BotMessageSquare className="hidden h-4 w-4 text-orange-600 transition group-hover:translate-x-0.5 sm:block" />
			</button>
		</div>
	);
}
