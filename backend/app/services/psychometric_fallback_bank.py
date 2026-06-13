from __future__ import annotations

from typing import Any

_TRAITS = {
    "analytical",
    "creativity",
    "execution",
    "collaboration",
    "risk_tolerance",
    "learning_agility",
    "domain_curiosity",
}

_TRAIT_LABELS = {
    "analytical": "Analytical reasoning",
    "creativity": "Creative problem solving",
    "execution": "Execution discipline",
    "collaboration": "Collaboration style",
    "risk_tolerance": "Risk appetite",
    "learning_agility": "Learning agility",
    "domain_curiosity": "Domain curiosity",
}


FALLBACK_QUESTION_BANK: dict[str, list[dict[str, Any]]] = {
    "college_student": [
        {
            "trait_tag": "analytical",
            "question": "When debugging, what do you do first?",
            "options": [
                {"option_id": "a", "text": "Reproduce and isolate variables", "trait_effect": {"analytical": 0.18}},
                {"option_id": "b", "text": "Search online fixes quickly", "trait_effect": {"learning_agility": 0.12}},
                {"option_id": "c", "text": "Ask teammate for context", "trait_effect": {"collaboration": 0.14}},
                {"option_id": "d", "text": "Try patches and observe", "trait_effect": {"risk_tolerance": 0.12}},
            ],
        },
        {
            "trait_tag": "creativity",
            "question": "How do you approach open-ended project ideas?",
            "options": [
                {"option_id": "a", "text": "Combine ideas from different fields", "trait_effect": {"creativity": 0.18}},
                {"option_id": "b", "text": "Pick proven templates and improve", "trait_effect": {"execution": 0.12}},
                {"option_id": "c", "text": "Brainstorm with peers", "trait_effect": {"collaboration": 0.14}},
                {"option_id": "d", "text": "Follow strict specs only", "trait_effect": {"analytical": 0.1}},
            ],
        },
        {
            "trait_tag": "execution",
            "question": "What best describes your weekly study rhythm?",
            "options": [
                {"option_id": "a", "text": "Consistent daily milestones", "trait_effect": {"execution": 0.18}},
                {"option_id": "b", "text": "Deep sprints near deadlines", "trait_effect": {"risk_tolerance": 0.1}},
                {"option_id": "c", "text": "Rotate based on urgency", "trait_effect": {"learning_agility": 0.12}},
                {"option_id": "d", "text": "Pair-program for accountability", "trait_effect": {"collaboration": 0.14}},
            ],
        },
        {
            "trait_tag": "collaboration",
            "question": "In team projects, your natural role is?",
            "options": [
                {"option_id": "a", "text": "Coordinator and communicator", "trait_effect": {"collaboration": 0.18}},
                {"option_id": "b", "text": "Core builder", "trait_effect": {"execution": 0.14}},
                {"option_id": "c", "text": "Reviewer and quality checker", "trait_effect": {"analytical": 0.14}},
                {"option_id": "d", "text": "Idea generator", "trait_effect": {"creativity": 0.14}},
            ],
        },
        {
            "trait_tag": "risk_tolerance",
            "question": "How do you pick internship opportunities?",
            "options": [
                {"option_id": "a", "text": "Take challenging uncertain roles", "trait_effect": {"risk_tolerance": 0.18}},
                {"option_id": "b", "text": "Choose stable known domains", "trait_effect": {"execution": 0.12}},
                {"option_id": "c", "text": "Balance upside and fit", "trait_effect": {"analytical": 0.14}},
                {"option_id": "d", "text": "Follow mentor recommendation", "trait_effect": {"collaboration": 0.12}},
            ],
        },
        {
            "trait_tag": "learning_agility",
            "question": "When a new tool appears, you usually?",
            "options": [
                {"option_id": "a", "text": "Prototype with it quickly", "trait_effect": {"learning_agility": 0.18}},
                {"option_id": "b", "text": "Read docs end-to-end first", "trait_effect": {"analytical": 0.12}},
                {"option_id": "c", "text": "Wait until class or team adopts it", "trait_effect": {"execution": 0.1}},
                {"option_id": "d", "text": "Compare alternatives before trying", "trait_effect": {"domain_curiosity": 0.12}},
            ],
        },
        {
            "trait_tag": "domain_curiosity",
            "question": "Which project topics pull you naturally?",
            "options": [
                {"option_id": "a", "text": "Emerging real-world problems", "trait_effect": {"domain_curiosity": 0.18}},
                {"option_id": "b", "text": "Algorithmic challenge sets", "trait_effect": {"analytical": 0.12}},
                {"option_id": "c", "text": "Collaborative products", "trait_effect": {"collaboration": 0.12}},
                {"option_id": "d", "text": "Creative interaction ideas", "trait_effect": {"creativity": 0.14}},
            ],
        },
    ],
    "twelfth_student": [
        {
            "trait_tag": "analytical",
            "question": "When solving hard questions, you mostly?",
            "options": [
                {"option_id": "a", "text": "Break into smaller steps", "trait_effect": {"analytical": 0.18}},
                {"option_id": "b", "text": "Try examples first", "trait_effect": {"learning_agility": 0.12}},
                {"option_id": "c", "text": "Discuss with classmates", "trait_effect": {"collaboration": 0.14}},
                {"option_id": "d", "text": "Guess and adjust", "trait_effect": {"risk_tolerance": 0.1}},
            ],
        },
        {
            "trait_tag": "creativity",
            "question": "Your favorite school tasks are usually?",
            "options": [
                {"option_id": "a", "text": "Building new ideas or designs", "trait_effect": {"creativity": 0.18}},
                {"option_id": "b", "text": "Following clear problem sheets", "trait_effect": {"execution": 0.12}},
                {"option_id": "c", "text": "Explaining concepts to peers", "trait_effect": {"collaboration": 0.12}},
                {"option_id": "d", "text": "Researching unknown topics", "trait_effect": {"domain_curiosity": 0.14}},
            ],
        },
        {
            "trait_tag": "execution",
            "question": "How do you prepare for major exams?",
            "options": [
                {"option_id": "a", "text": "Follow a fixed study plan", "trait_effect": {"execution": 0.18}},
                {"option_id": "b", "text": "Study intensely near exam", "trait_effect": {"risk_tolerance": 0.1}},
                {"option_id": "c", "text": "Switch topics by mood", "trait_effect": {"learning_agility": 0.12}},
                {"option_id": "d", "text": "Study in group sessions", "trait_effect": {"collaboration": 0.14}},
            ],
        },
        {
            "trait_tag": "collaboration",
            "question": "In group assignments, you usually?",
            "options": [
                {"option_id": "a", "text": "Coordinate tasks and deadlines", "trait_effect": {"collaboration": 0.18}},
                {"option_id": "b", "text": "Finish your part independently", "trait_effect": {"execution": 0.14}},
                {"option_id": "c", "text": "Check accuracy of outputs", "trait_effect": {"analytical": 0.12}},
                {"option_id": "d", "text": "Suggest creative approaches", "trait_effect": {"creativity": 0.14}},
            ],
        },
        {
            "trait_tag": "risk_tolerance",
            "question": "When choosing electives, you prefer?",
            "options": [
                {"option_id": "a", "text": "New and challenging topics", "trait_effect": {"risk_tolerance": 0.18}},
                {"option_id": "b", "text": "Subjects with predictable scoring", "trait_effect": {"execution": 0.12}},
                {"option_id": "c", "text": "Subjects friends choose", "trait_effect": {"collaboration": 0.1}},
                {"option_id": "d", "text": "Topics aligned to goals", "trait_effect": {"analytical": 0.14}},
            ],
        },
        {
            "trait_tag": "learning_agility",
            "question": "If a topic changes suddenly, you?",
            "options": [
                {"option_id": "a", "text": "Adapt quickly and continue", "trait_effect": {"learning_agility": 0.18}},
                {"option_id": "b", "text": "Need full notes first", "trait_effect": {"analytical": 0.12}},
                {"option_id": "c", "text": "Practice with short quizzes", "trait_effect": {"execution": 0.12}},
                {"option_id": "d", "text": "Ask mentor for strategy", "trait_effect": {"collaboration": 0.12}},
            ],
        },
        {
            "trait_tag": "domain_curiosity",
            "question": "Outside classes, what do you explore most?",
            "options": [
                {"option_id": "a", "text": "Future careers and technologies", "trait_effect": {"domain_curiosity": 0.18}},
                {"option_id": "b", "text": "Challenging puzzles", "trait_effect": {"analytical": 0.12}},
                {"option_id": "c", "text": "Creative content", "trait_effect": {"creativity": 0.12}},
                {"option_id": "d", "text": "Team activities", "trait_effect": {"collaboration": 0.12}},
            ],
        },
    ],
}

GUIDED_QUESTION_VARIANTS: dict[str, list[dict[str, Any]]] = {
    "analytical": [
        {
            "question": "A task feels unclear. What do you do first?",
            "options": [
                {"option_id": "a", "text": "Break it into known and unknown parts", "trait_effect": {"analytical": 0.18}},
                {"option_id": "b", "text": "Ask someone to explain the goal", "trait_effect": {"collaboration": 0.12}},
                {"option_id": "c", "text": "Try examples until the pattern appears", "trait_effect": {"learning_agility": 0.12}},
                {"option_id": "d", "text": "Start quickly and adjust later", "trait_effect": {"risk_tolerance": 0.1}},
            ],
        },
        {
            "question": "When two answers seem correct, you usually?",
            "options": [
                {"option_id": "a", "text": "Compare assumptions behind both", "trait_effect": {"analytical": 0.18}},
                {"option_id": "b", "text": "Choose the one that feels practical", "trait_effect": {"execution": 0.12}},
                {"option_id": "c", "text": "Discuss it with peers", "trait_effect": {"collaboration": 0.12}},
                {"option_id": "d", "text": "Explore a third possibility", "trait_effect": {"creativity": 0.12}},
            ],
        },
    ],
    "creativity": [
        {
            "question": "You get a broad project brief. Your first move?",
            "options": [
                {"option_id": "a", "text": "Sketch several possible directions", "trait_effect": {"creativity": 0.18}},
                {"option_id": "b", "text": "Find a proven example to follow", "trait_effect": {"execution": 0.12}},
                {"option_id": "c", "text": "List constraints and success metrics", "trait_effect": {"analytical": 0.12}},
                {"option_id": "d", "text": "Ask teammates for ideas", "trait_effect": {"collaboration": 0.12}},
            ],
        },
        {
            "question": "How do you improve a boring assignment?",
            "options": [
                {"option_id": "a", "text": "Add a fresh angle or use case", "trait_effect": {"creativity": 0.18}},
                {"option_id": "b", "text": "Make it cleaner and more complete", "trait_effect": {"execution": 0.12}},
                {"option_id": "c", "text": "Research real-world examples", "trait_effect": {"domain_curiosity": 0.12}},
                {"option_id": "d", "text": "Ask for feedback early", "trait_effect": {"collaboration": 0.12}},
            ],
        },
    ],
    "execution": [
        {
            "question": "A deadline moves closer. What changes first?",
            "options": [
                {"option_id": "a", "text": "Prioritize the minimum complete version", "trait_effect": {"execution": 0.18}},
                {"option_id": "b", "text": "Work longer near the deadline", "trait_effect": {"risk_tolerance": 0.1}},
                {"option_id": "c", "text": "Ask the group to divide tasks", "trait_effect": {"collaboration": 0.12}},
                {"option_id": "d", "text": "Recheck what actually matters", "trait_effect": {"analytical": 0.12}},
            ],
        },
        {
            "question": "How do you recover after missing a study target?",
            "options": [
                {"option_id": "a", "text": "Reset the plan for the next day", "trait_effect": {"execution": 0.18}},
                {"option_id": "b", "text": "Switch to a more interesting topic", "trait_effect": {"learning_agility": 0.1}},
                {"option_id": "c", "text": "Ask someone to keep you accountable", "trait_effect": {"collaboration": 0.12}},
                {"option_id": "d", "text": "Analyze why the plan failed", "trait_effect": {"analytical": 0.12}},
            ],
        },
    ],
    "collaboration": [
        {
            "question": "A teammate is stuck. You usually?",
            "options": [
                {"option_id": "a", "text": "Help them unblock the next step", "trait_effect": {"collaboration": 0.18}},
                {"option_id": "b", "text": "Take over the task briefly", "trait_effect": {"execution": 0.12}},
                {"option_id": "c", "text": "Diagnose the root issue together", "trait_effect": {"analytical": 0.12}},
                {"option_id": "d", "text": "Suggest a different approach", "trait_effect": {"creativity": 0.12}},
            ],
        },
        {
            "question": "In a new group, how do you contribute early?",
            "options": [
                {"option_id": "a", "text": "Clarify roles and communication", "trait_effect": {"collaboration": 0.18}},
                {"option_id": "b", "text": "Start building the first deliverable", "trait_effect": {"execution": 0.12}},
                {"option_id": "c", "text": "Share research and references", "trait_effect": {"domain_curiosity": 0.12}},
                {"option_id": "d", "text": "Challenge assumptions politely", "trait_effect": {"analytical": 0.12}},
            ],
        },
    ],
    "risk_tolerance": [
        {
            "question": "A high-upside opportunity feels uncertain. You?",
            "options": [
                {"option_id": "a", "text": "Try it with a backup plan", "trait_effect": {"risk_tolerance": 0.18}},
                {"option_id": "b", "text": "Choose the safer proven path", "trait_effect": {"execution": 0.12}},
                {"option_id": "c", "text": "Compare risks before deciding", "trait_effect": {"analytical": 0.12}},
                {"option_id": "d", "text": "Ask a mentor first", "trait_effect": {"collaboration": 0.12}},
            ],
        },
        {
            "question": "When learning something difficult, you prefer?",
            "options": [
                {"option_id": "a", "text": "Jump into a challenging task", "trait_effect": {"risk_tolerance": 0.18}},
                {"option_id": "b", "text": "Follow a structured beginner path", "trait_effect": {"execution": 0.12}},
                {"option_id": "c", "text": "Experiment with small examples", "trait_effect": {"learning_agility": 0.12}},
                {"option_id": "d", "text": "Understand the theory first", "trait_effect": {"analytical": 0.12}},
            ],
        },
    ],
    "learning_agility": [
        {
            "question": "A new tool becomes important suddenly. You?",
            "options": [
                {"option_id": "a", "text": "Build a small test with it", "trait_effect": {"learning_agility": 0.18}},
                {"option_id": "b", "text": "Read the official guide first", "trait_effect": {"analytical": 0.12}},
                {"option_id": "c", "text": "Wait for a class or mentor", "trait_effect": {"collaboration": 0.1}},
                {"option_id": "d", "text": "Use it only when required", "trait_effect": {"execution": 0.1}},
            ],
        },
        {
            "question": "If your plan stops working, you usually?",
            "options": [
                {"option_id": "a", "text": "Change method and keep moving", "trait_effect": {"learning_agility": 0.18}},
                {"option_id": "b", "text": "Review the goal again", "trait_effect": {"analytical": 0.12}},
                {"option_id": "c", "text": "Ask someone for a shortcut", "trait_effect": {"collaboration": 0.1}},
                {"option_id": "d", "text": "Push harder on the old plan", "trait_effect": {"execution": 0.1}},
            ],
        },
    ],
    "domain_curiosity": [
        {
            "question": "What makes a career path exciting to you?",
            "options": [
                {"option_id": "a", "text": "It solves important real problems", "trait_effect": {"domain_curiosity": 0.18}},
                {"option_id": "b", "text": "It has clear growth steps", "trait_effect": {"execution": 0.12}},
                {"option_id": "c", "text": "It involves hard puzzles", "trait_effect": {"analytical": 0.12}},
                {"option_id": "d", "text": "It lets me create new things", "trait_effect": {"creativity": 0.12}},
            ],
        },
        {
            "question": "Outside class, what pulls your attention?",
            "options": [
                {"option_id": "a", "text": "Emerging fields and use cases", "trait_effect": {"domain_curiosity": 0.18}},
                {"option_id": "b", "text": "Hands-on project tutorials", "trait_effect": {"learning_agility": 0.12}},
                {"option_id": "c", "text": "Competitions and challenges", "trait_effect": {"risk_tolerance": 0.1}},
                {"option_id": "d", "text": "Team activities and communities", "trait_effect": {"collaboration": 0.12}},
            ],
        },
    ],
}


def fallback_traits_coverage(user_type: str) -> set[str]:
    questions = FALLBACK_QUESTION_BANK.get(user_type, [])
    return {item["trait_tag"] for item in questions}


def has_full_fallback_coverage() -> bool:
    return all(_TRAITS.issubset(fallback_traits_coverage(user_type)) for user_type in FALLBACK_QUESTION_BANK)


def select_fallback_question(
    *,
    user_type: str,
    asked_trait_tags: set[str],
    position: int,
    current_traits: dict[str, float] | None = None,
    recent_answers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    questions = FALLBACK_QUESTION_BANK.get(user_type) or FALLBACK_QUESTION_BANK["college_student"]

    if current_traits:
        ordered_traits = sorted(
            (trait for trait in _TRAITS if trait in current_traits),
            key=lambda trait: (float(current_traits.get(trait, 0.5)), trait),
        )
        target_trait = next(
            (trait for trait in ordered_traits if trait not in asked_trait_tags),
            ordered_traits[0] if ordered_traits else None,
        )
        if target_trait:
            variants = GUIDED_QUESTION_VARIANTS.get(target_trait) or []
            if variants:
                variant = dict(variants[position % len(variants)])
                recent_trait = ""
                if recent_answers:
                    recent_trait = str((recent_answers[-1] or {}).get("trait_tag") or "")
                variant["trait_tag"] = target_trait
                variant["ai_status"] = "guided_adaptive"
                variant["next_focus"] = _TRAIT_LABELS.get(target_trait, target_trait)
                if recent_trait and recent_trait != target_trait:
                    variant["adaptation_reason"] = (
                        f"Shifting from {recent_trait.replace('_', ' ')} to "
                        f"{target_trait.replace('_', ' ')} because confidence is still forming."
                    )
                else:
                    variant["adaptation_reason"] = (
                        f"Testing {target_trait.replace('_', ' ')} because confidence is still forming."
                    )
                return variant

    for item in questions:
        if item["trait_tag"] not in asked_trait_tags:
            payload = dict(item)
            payload["ai_status"] = "guided_adaptive"
            payload["next_focus"] = _TRAIT_LABELS.get(item["trait_tag"], item["trait_tag"])
            payload["adaptation_reason"] = (
                f"Checking {item['trait_tag'].replace('_', ' ')} to balance the profile."
            )
            return payload

    payload = dict(questions[position % len(questions)])
    payload["ai_status"] = "guided_adaptive"
    payload["next_focus"] = _TRAIT_LABELS.get(payload["trait_tag"], payload["trait_tag"])
    payload["adaptation_reason"] = (
        f"Rechecking {payload['trait_tag'].replace('_', ' ')} to improve confidence."
    )
    return payload
