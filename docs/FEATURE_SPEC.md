# Feature Specification

## Product Name

SAGE AI Career Navigator

## Product Type

Internal SAGE/SIRT Student Success OS.

## Primary Outcomes

- Improve admission counseling quality.
- Reduce wrong-branch decisions.
- Improve student readiness.
- Improve placement-cell planning.
- Make training investment measurable.
- Give leadership admissions and placement intelligence.

## User Roles

This section describes the target-state role experience; currently implemented capabilities are listed separately below.

### Prospective Student

Target experience: configurable branch/program fit, expectation reality checks, and first 100-day roadmaps.

### Admission Counselor

Target experience: Counselor Copilot, branch comparison talking points, parent concern summaries, and follow-up recommendations.

### College Student

Target experience: career analysis, skill gaps, resume analysis, employability, internship readiness, company fit, and outcome simulation.

### Faculty Mentor

Target experience: Personal AI Faculty Advisor notes and intervention priorities.

### Placement Cell

Target experience: Skill Evidence Ledger, Company-Specific Readiness Radar, AI Placement War Room, cohort heatmaps, and training recommendations.

### Leadership

Target experience: Admission Conversion Intelligence, Lost Admission Reason Analyzer, branch demand insights, readiness trends, and Training ROI Engine.

## Current Implemented Features

| Area | Implemented Capability |
| --- | --- |
| Auth | Register, login, logout, current user |
| Student Profile | Create, list, view, edit |
| Career Analysis | Roles, skill gaps, roadmap, salary, industry trends |
| Program Fit Analysis | Configurable SAGE institution catalog, generic program-fit contract, counselor expectation checks, and AIML/Cyber compatibility fields |
| Admission Intelligence | Admin-only metrics, high-intent and wrong-branch-risk lead cards, Counselor Copilot briefs, and lost-reason signals from existing twelfth-student profiles |
| Placement Intelligence | Admin-only Skill Evidence Ledger, Company-Specific Readiness Radar, AI Placement War Room, Faculty Advisor notes, Outcome Simulation proxy, and Training ROI signals from existing college-student readiness records |
| RAG Evidence | Seeded SAGE/SIRT knowledge retrieval, DB-backed admin text/PDF/DOCX sources, pgvector-ready semantic retrieval for embedded admin chunks, persisted `rag_evidence`, and frontend evidence snippets for program-fit analysis |
| RAG Governance | Admin source review lifecycle with pending/approved/rejected status, review notes, expiry, freshness labels, and retrieval gating for active approved current sources |
| Resume | URL-backed PDF/DOCX analysis with stored file copy |
| Psychometric | Adaptive session, fallback questions, trait scoring |
| Employability | Score generation and retrieval |
| Placement Risk | Risk generation and retrieval |
| Company Fit | Company match generation and retrieval |
| Role Gaps | Missing skills and learning plan |
| Internship | Readiness score and action plan |
| Training | Cohort-level training recommendations |
| Admin | Metrics and student overview |
| Admin Readiness | System readiness indicators, RAG governance counts, failed job/embedding counts, student filters, and CSV export |
| Institution Admin | Override API for thresholds, priority skills, and counselor notes |
| Async Jobs | Analysis job dispatch, status polling, and agentic snapshot summary |
| Agentic Snapshot | Agent stages, verifier status, confidence, evidence count, warnings, blocked snapshot reporting, and next-best actions |

## Phase 2 Configurable Institution Model

Phase 2 adds the configurable SAGE institution catalog, program-fit analysis contract, counselor expectation checks, and admin override API. The previous AIML/Cyber-specific fields remain available as compatibility fields during the transition.

## Phase 4 Seeded RAG Foundation

Phase 4 adds seeded RAG retrieval over curated SAGE/SIRT knowledge. Program-fit analysis now stores retrieved evidence snippets and the frontend shows the evidence used.

## Phase 5 Agentic Analysis Snapshot

Phase 5 adds an agentic analysis snapshot over the existing modules. The async job summary now records agent stages, verifier status, confidence, evidence count, warnings, and next-best actions. This is deterministic orchestration around current modules, not autonomous tool-calling agents.

## Phase 6 Document RAG Expansion

Phase 6 adds a DB-backed institutional knowledge layer. Admins can add text knowledge sources or upload PDF/DOCX files from the admin dashboard for programs, counseling, placement, skills, resumes, training, and policies; activate or deactivate sources; and view chunk counts. Existing RAG retrieval now merges seeded chunks with active admin-managed chunks. New admin chunks get embeddings, production Postgres can use the pgvector migration for semantic ranking, lexical retrieval remains the fallback, and admins can trigger embedding reindexing for missing or failed chunk embeddings. The institutional readiness wave adds source review governance: new admin text/PDF/DOCX sources default to pending review, existing migrated sources stay approved, and retrieval only uses active approved non-expired admin sources. Scheduled recurring indexing remains a later upgrade.

## Phase 7 Admission Intelligence Baseline

Phase 7 adds the first Admission Intelligence Command Center baseline. The current implementation is deterministic and derived from existing `twelfth_student` profiles plus the latest program-fit analyses. Admins can view admission metrics, high-intent and wrong-branch-risk lead cards, Counselor Copilot briefs, and lost-admission reason signals. CRM imports, counselor assignment, admission status tracking, outbound communication, and conversion funnel attribution remain later upgrades.

## Phase 8 Placement Intelligence Baseline

Phase 8 adds the first Placement Intelligence Command Center baseline. The current implementation is deterministic and derived from existing college-student profiles plus latest employability, placement risk, company fit, role gap, career analysis, and internship readiness records. Admins can view placement metrics, priority student signals, Skill Evidence Ledger details, Company-Specific Readiness Radar, Faculty Advisor notes, Outcome Simulation proxy status, and Training ROI signals.

The placement operations layer now adds a lightweight TnP workflow without becoming a full ATS: admins manage placement/internship opportunities, company master records, linked recruiter contact metadata, eligibility, package or stipend labels, vacancies, hiring stages, eligible-student shortlists, application status lanes, review notes, next-step instructions, due dates, and CSV exports. Students see matched opportunities inside the internship readiness loop, mark interest or applied status, maintain their own note while the application is still student-editable, and see placement-cell notes plus next-step instructions when admins advance the pipeline. External recruiter imports, interview calendar automation, offer-document workflows, notifications, faculty assignment workflows, and historical before/after training measurement remain later upgrades.

## Target Features

### Admission Intelligence Command Center

- Expectation Reality Check. Implemented through program-fit analysis.
- Counselor Copilot. Implemented baseline in the admin Admission Intelligence panel.
- Admission Conversion Intelligence. Baseline metrics implemented; full funnel attribution remains later.
- Lost Admission Reason Analyzer. Implemented baseline through deterministic lost-reason signals.
- High-intent undecided student tracking. Implemented baseline through derived lead cards.
- First 100-day roadmap. Program-fit first-year roadmap is surfaced in counselor briefs.

### Placement Intelligence Command Center

- Student Skill Evidence Ledger.
- Company-Specific Readiness Radar. Implemented baseline from latest company-fit scores.
- AI Placement War Room. Implemented baseline through priority student cards.
- Personal AI Faculty Advisor. Implemented baseline through intervention notes.
- Outcome Simulation. Implemented proxy through expected readiness lift and evidence scoring.
- Training ROI Engine. Implemented baseline through aggregated missing-skill signals.
- Placement opportunity lifecycle. Implemented lightweight opportunity board, company master linkage, eligible-student shortlists, student application tracking, admin review notes, pipeline statuses, next-step instructions, and CSV exports.

### AI And RAG

- AWS Bedrock native model provider support through the Phase 3 provider abstraction. The OpenAI-compatible provider remains the default fallback until production Bedrock credentials and model governance are validated.
- Seeded institution-specific RAG foundation for program-fit evidence.
- Agentic analysis orchestrator and verifier agent baseline.
- DB-backed document RAG baseline for admin-managed institutional knowledge.
- Vector semantic RAG upgrade with embeddings and pgvector for admin-managed text/PDF/DOCX sources. Implemented for new chunks, with admin-triggered reindexing for missing or failed embeddings; scheduled indexing remains later.
- Evidence snippets and citations.

## First Production Pass Boundaries

The first production pass does not include public SaaS billing, full multi-tenant onboarding, a mobile app, payment workflows, or full integration with every university system.
