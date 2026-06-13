# SAGE AI Career Navigator Design

## Summary

SAGE AI Career Navigator will evolve from a working career-advice prototype into an internal SAGE/SIRT Student Success OS. It will support the full student lifecycle from admission and branch choice to college skill development, internship readiness, resume improvement, placement risk management, and placement-cell strategy.

The product will first target SAGE/SIRT as an institutional platform, with an architecture that can later become a SaaS product for other colleges and universities.

## Product Positioning

The core pitch is:

> SAGE AI Career Navigator connects student profile, branch decision, skill roadmap, employability, and placement outcome in one institution-specific intelligence platform.

The product should not be positioned as a generic chatbot. It should be positioned as an institutional intelligence system grounded in SAGE program data, placement rules, student evidence, and AI validation.

The headline wow-factor pillars are the Admission Intelligence Command Center and the Placement Intelligence Command Center.

Admission Intelligence Command Center pitch:

> SAGE AI Career Navigator improves admissions quality by helping students understand the reality of each branch, helping counselors guide better conversations, and helping leadership learn why students convert or drop.

Placement Intelligence Command Center pitch:

> SAGE AI Career Navigator does not only recommend careers. It converts student data into placement action: evidence-backed skills, company readiness, faculty interventions, placement war-room planning, outcome simulation, and training ROI.

## Target Users

### 12th Students And Admission Counselors

The system helps prospective students select the right school, program, and branch. It compares student academics, interests, aptitude indicators, and career goals against configured SAGE programs and produces transparent recommendations.

Expected outputs:

- Best-fit schools, programs, and branches.
- Fit score and confidence.
- Reasons for fit and risk.
- Career paths linked to each recommendation.
- Salary and demand context.
- First-year readiness roadmap.
- Expectation Reality Check for each considered branch.
- Counselor Copilot summary for admission conversations.
- Admission conversion and lost-reason intelligence for leadership.

### College Students

The system helps current students improve placement readiness continuously.

Expected outputs:

- Career recommendations.
- Skill gaps.
- Learning roadmap.
- Resume analysis.
- Internship readiness.
- Company fit.
- Placement risk.
- Personal intervention plan.

### Placement Cell And Faculty

The system helps placement teams and faculty identify cohort-level readiness gaps and intervene early.

Expected outputs:

- Cohort readiness dashboard.
- Weak-skill heatmaps.
- High-risk student list.
- Training recommendations.
- Company-readiness segmentation.
- Department and program-level trends.
- Skill evidence gaps by student and cohort.
- Placement drive war-room planning.
- Weekly AI faculty advisor notes.

### Institutional Leadership

The system helps leadership understand admissions, training, and placement outcomes.

Expected outputs:

- Branch demand visibility.
- Student readiness trends.
- Placement outcome risk.
- Training ROI indicators.
- Strategic recommendations for admissions and placement planning.
- Evidence-backed view of whether institutional training improves placement readiness.
- Admission conversion insights by school, program, branch, counselor, and lead source.
- Lost admission reason patterns that explain why high-intent students did not enroll.

## Admission Intelligence Command Center

The command center addresses a hidden institutional pain point: many students choose a branch with incomplete expectations, social pressure, parent pressure, or salary myths. The institution usually discovers the mismatch months later through low engagement, poor performance, dissatisfaction, branch-change requests, or weak placement readiness.

### Expectation Reality Check

The system should explain what each branch or program actually means before the student commits.

For each considered branch, the system should show:

- Core subjects.
- Difficulty level.
- Required skills.
- Common misconceptions.
- Realistic career paths.
- Salary and demand context.
- Type of student who usually succeeds.
- First-year preparation needs.

Example:

> AI/ML is not only about using AI tools. It requires math, Python, statistics, data handling, and consistent project work.

This helps students and parents make a realistic decision instead of chasing a trend.

### Counselor Copilot

Admission counselors should get an AI-prepared conversation brief before or during counseling.

The brief should include:

- Student profile summary.
- Best-fit programs and branches.
- Branch comparison talking points.
- Likely hesitation points.
- Parent concerns to address.
- Expectation Reality Check highlights.
- Suggested follow-up.
- First 100-day roadmap after admission.

This makes counseling more consistent, evidence-backed, and scalable across counselors.

### Admission Conversion Intelligence

The system should track counseling and admission funnel signals so leadership can understand demand and improve conversion.

Tracked insights should include:

- Student interest by school, program, and branch.
- Most compared branches.
- Common objections.
- Parent concern patterns.
- Counselor follow-up status.
- High-intent but undecided students.
- Conversion by branch, program, counselor, and lead source.

This turns counseling interactions into institutional strategy data.

### Lost Admission Reason Analyzer

When a student does not enroll, the system should classify the reason instead of losing the learning.

Reason categories should include:

- Fees.
- Branch confusion.
- Parent objection.
- Competitor college.
- Location.
- Unclear career outcome.
- Scholarship issue.
- Delayed follow-up.
- Low trust in placement outcomes.

This helps SAGE/SIRT reduce avoidable lost admissions and improve counselor messaging.

## Placement Intelligence Command Center

The placement command center addresses another hidden institutional pain point: colleges do not just need student advice; they need an operating system that turns student evidence into placement action before placement season.

### Student Skill Evidence Ledger

Every claimed skill should have evidence. Evidence can include:

- Resume line.
- Project.
- Certification.
- Internship.
- Psychometric or quiz signal.
- GitHub, portfolio, or demo link.
- Faculty validation.

The ledger helps the placement cell separate claimed skills from verified readiness.

### Company-Specific Readiness Radar

The system should evaluate students against each company or role and classify readiness:

- Ready now.
- Almost ready.
- Not eligible.
- Needs intervention.

The radar should show why a student is not ready: eligibility issue, missing skill, weak resume, missing project evidence, internship gap, or low interview confidence.

### AI Placement War Room

Before a placement drive, the placement cell should see an operational dashboard:

- Eligible students.
- Near-miss students.
- Company-wise skill gaps.
- Resume-risk students.
- Suggested last-mile training.
- Faculty intervention priorities.
- Student shortlists by readiness band.

This converts the product from analytics into placement operations.

### Personal AI Faculty Advisor

Faculty mentors should receive weekly advisor notes for their assigned students:

- Students ready for company shortlisting.
- Students with urgent resume issues.
- Students missing internships or project evidence.
- Students drifting off-track.
- Recommended faculty actions.

This helps faculty intervene early without manually reviewing every profile.

### Outcome Simulation

Students, faculty, and placement teams should be able to simulate readiness improvements:

- Add one project.
- Complete one certification.
- Improve resume.
- Finish a training module.
- Add internship evidence.

The simulation should estimate how those actions affect employability, company readiness, placement risk, and internship readiness.

### Training ROI Engine

The system should measure whether training programs improve outcomes:

- Before and after skill readiness.
- Before and after company eligibility.
- Resume quality delta.
- Placement risk delta.
- Cohort-level improvement.
- Suggested next training investment.

This makes institutional training decisions more measurable and defensible.

## Current System Baseline

The existing codebase already provides a strong foundation:

- FastAPI backend with SQLAlchemy, Pydantic, Alembic, JWT auth, and rate limits.
- Next.js frontend with TypeScript, Tailwind, Recharts, and role-aware pages.
- PostgreSQL/Supabase-compatible database model.
- Current LLM integration through an OpenAI-compatible client, with target migration to AWS Bedrock native model APIs.
- Strict Pydantic schemas for AI outputs.
- JSON repair and output normalization.
- LLM cost controls, prompt limits, endpoint budgets, and circuit breaker.
- Async analysis jobs using the Celery/Redis pattern.
- Psychometric quiz flow with LLM generation and fallback questions.
- Existing modules for career analysis, employability, resume analysis, company fit, role gaps, placement risk, internship readiness, training recommendations, and admin dashboards.
- Phase 5 agentic snapshot metadata over async analysis jobs, including agent stages, verifier status, confidence, warnings, blockers, evidence count, and next-best actions.

The remaining AI limitation is that the agentic workflow is deterministic orchestration around existing modules. It is not yet an autonomous tool-calling multi-agent system, and it does not yet use historical outcomes to learn intervention impact.

## Scope

The first production-ready vision should include both admission intelligence and placement intelligence. It should support all SAGE schools and branches from the start through a configurable program system.

The system should avoid hardcoded branch comparisons such as AIML versus Cyber Security as the long-term architecture. Those can exist only as seeded examples within a broader configurable model.

## Institution Configuration Model

The platform will use a hybrid source of truth:

- Seeded SAGE/SIRT data for fast launch and ceremony readiness.
- Limited admin controls for high-value configuration.

Seeded data should include:

- Schools.
- Programs.
- Branches and specializations.
- Career pathways.
- Role maps.
- Required skills.
- Recommended skills.
- Salary bands.
- Industry demand notes.
- Eligibility rules.
- Placement thresholds.
- Training programs.

Admin-editable controls should initially include:

- Priority skills per branch or pathway.
- Training program mappings.
- Placement readiness thresholds.
- Risk intervention rules.
- Company eligibility rules.

This gives the judges a production-grade story without forcing a full admin CMS in the first implementation phase.

## System Architecture

The production architecture should preserve the existing stack while changing the intelligence layer.

### Frontend

- Next.js App Router.
- TypeScript.
- Tailwind.
- Recharts.
- Role-aware student and admin dashboards.

### Backend

- FastAPI.
- SQLAlchemy 2.0.
- Pydantic v2.
- Alembic migrations.
- JWT cookie auth.
- Rate limiting.
- Structured error handling.

### Database

- PostgreSQL on Supabase for the current launch path.
- Seeded RAG retrieval is implemented through a curated backend knowledge store.
- DB-backed admin-managed text knowledge sources are implemented for document RAG.
- Future vector retrieval through Supabase vector or Postgres pgvector.

### AI Layer

The current async analysis flow now acts as a deterministic analysis orchestrator. It records one coherent student intelligence snapshot with stage metadata and verifier output instead of only disconnected module IDs.

The snapshot should include:

- Recommended school, program, or branch fit.
- Career pathways.
- Skill gaps.
- Learning roadmap.
- Employability score.
- Placement risk.
- Company fit.
- Internship readiness.
- Suggested interventions.
- Evidence summary.
- Confidence summary.
- Agent stage metadata.
- Verifier status and next-best actions.

### Deployment Layer

Current deployment direction:

- Frontend: Vercel.
- Database: Supabase.
- Backend: Google Cloud Run as the primary launch target.

Deployment rationale:

- Cloud Run gives a low-cost, scalable, managed container path for the FastAPI backend.
- Vercel remains a good low-cost path for the Next.js frontend.
- Supabase remains a good low-cost path for Postgres during launch.
- Railway remains temporary only and should not be part of the final launch-readiness story.

The target production story is a less-cost, scalable, and reliable institutional deployment: Vercel frontend, Google Cloud Run backend, Supabase Postgres, and AWS Bedrock for managed native LLM access.

## AI, ML, And RAG Design

The AI architecture should be presented as a multi-agent student success intelligence system backed by deterministic scoring and institution-specific RAG.

The target LLM provider is AWS Bedrock using Amazon native LLMs supported by the available sandbox account. The Phase 3 provider abstraction keeps the current OpenAI-compatible provider available while allowing Bedrock selection through environment settings. The production AI provider abstraction supports provider selection, model configuration, timeouts, retries, and structured-output validation.

### Agent Roles

#### Profile Understanding Agent

Normalizes academics, interests, skills, projects, internships, certifications, psychometric signals, and resume facts.

#### Program Fit Agent

Compares student profile data against configured SAGE schools, programs, branches, and eligibility rules.

#### Career Pathway Agent

Maps strong-fit branches or programs to roles, salary bands, market demand, long-term outcomes, and learning priorities.

#### Skill Gap Agent

Compares current capabilities against target pathways and produces actionable learning gaps.

#### Resume Agent

Extracts resume evidence, identifies weak sections, detects missing keywords, and recommends improvements.

#### Placement Risk Agent

Predicts readiness risk using CGPA, skills, projects, internships, resume quality, psychometric confidence, and pathway fit.

#### Training Strategy Agent

Aggregates student and cohort gaps into faculty and placement-cell training recommendations.

#### Verifier Agent

Checks AI outputs for schema validity, unsupported claims, unrealistic salary ranges, recommendation conflicts, missing evidence, and inconsistency with configured institutional rules.

Phase 5 implements the first deterministic version of this agent through `AnalysisVerifierService`. It checks module completeness, evidence count, warnings, blockers, confidence, and next-best actions for the async analysis snapshot.

### Deterministic Scoring

The system should keep deterministic scoring for:

- Employability score.
- Placement risk.
- Company fit.
- Internship readiness.
- Basic eligibility.

LLM or agent adjustments may be used only within bounded limits. This keeps the system explainable and safer than allowing the LLM to decide everything.

### RAG Knowledge Layer

The RAG layer makes the product institution-specific. Phase 4 implements the seeded baseline: curated SAGE/SIRT chunks, deterministic retrieval, authenticated search, bounded evidence context in program-fit analysis, persisted `rag_evidence`, and frontend evidence snippets. Phase 6 implements the DB-backed document baseline: admin text sources, generated chunks, activate/deactivate governance, merged seeded plus admin retrieval, and an admin knowledge panel.

Initial knowledge sources:

- SAGE/SIRT school and program information.
- Branch and specialization details.
- Syllabus and skill maps.
- Placement rules and eligibility rules.
- Company criteria.
- Training calendars.
- Resume templates and placement guidelines.
- Admission counseling FAQs.
- Industry reports and role definitions.
- Salary benchmark notes.

Agent usage:

- Program Fit Agent retrieves program and branch details.
- Career Pathway Agent retrieves role and market knowledge.
- Skill Gap Agent retrieves pathway skill maps.
- Resume Agent retrieves institution-approved resume standards.
- Placement Risk Agent retrieves eligibility rules and historical patterns.
- Training Strategy Agent retrieves training history and outcomes.
- Verifier Agent checks generated claims against retrieved evidence.

RAG implementation path:

1. Seed static institutional knowledge in structured JSON or Markdown. Implemented in Phase 4.
2. Add retrieval service over seeded knowledge. Implemented in Phase 4.
3. Add admin-managed text sources and lifecycle controls. Implemented in Phase 6.
4. Add Supabase vector or Postgres pgvector for semantic retrieval. Implemented for admin-managed chunks in the 2026-05-23 semantic RAG pass.
5. Add PDF/DOCX upload/parsing and background indexing for rules, syllabi, and training docs. PDF/DOCX upload/parsing is implemented; scheduled indexing remains a later upgrade.
6. Show evidence snippets and citations in student and admin UI. Implemented for program-fit evidence in Phase 4; broader citations remain a target.

## Production Rules

The system must follow these rules:

- Do not show blind LLM output directly.
- Validate every AI output with strict schemas.
- Attach reason, evidence, and confidence to major recommendations.
- Degrade gracefully with config-derived or rule-derived outputs where possible.
- Mark AI-generated, rule-derived, and config-derived insights clearly in internal metadata.
- Keep raw chain-of-thought hidden.
- Show a professional reasoning pipeline instead: profile parsed, evidence retrieved, fit scored, risk checked, verified, final recommendation generated.

## Feature Roadmap

### Phase 1: Foundation And Documentation

Goal: make the project understandable, pitch-ready, and implementation-ready.

Deliverables:

- Rewrite README for product, setup, deployment, and demo flow.
- Create `SYSTEM_AUDIT.md`.
- Add feature specification document.
- Add tech stack document.
- Add system architecture document.
- Add AI/ML/RAG design document.
- Add deployment strategy document.
- Document current implemented versus planned capabilities.

### Phase 2: Configurable Institution Model

Goal: replace hardcoded branch thinking with a configurable SAGE academic model.

Deliverables:

- Seed schools, programs, branches, pathways, skills, roles, and rules.
- Add backend schemas and services for program intelligence.
- Replace hardcoded AIML versus Cyber Security branch analysis with configurable branch/program fit.
- Add admin-visible configuration summary.
- Add limited admin controls for skills, thresholds, and training mappings.

### Phase 3: LLM Provider Abstraction

Goal: make inference provider selection production-ready while preserving local fallback behavior.

Deliverables:

- Add provider configuration.
- Keep OpenAI-compatible provider support.
- Add AWS Bedrock provider selection.
- Add native Bedrock request/response handling through the provider abstraction.
- Preserve budgets, retries, circuit breaker behavior, and schema validation.

Status: implemented.

### Phase 4: RAG Knowledge Base

Goal: ground recommendations in SAGE-specific evidence.

Deliverables:

- Add seeded knowledge store.
- Add retrieval service.
- Add authenticated RAG search API.
- Persist retrieved evidence on program-fit analyses.
- Add evidence snippets in the Program Intelligence UI.

Status: seeded baseline implemented. Admin-managed text/PDF/DOCX sources are implemented in Phase 6. Semantic vector search and admin-triggered embedding reindexing are implemented. Scheduled indexing, source review, and broader citation coverage remain later work.

### Phase 5: Agentic Analysis Orchestrator

Goal: convert independent LLM calls into one coherent student intelligence workflow.

Deliverables:

- Extend the existing analysis snapshot service as the orchestrator.
- Add agent stage metadata.
- Add verifier pass.
- Produce a unified student intelligence snapshot in `analysis_jobs.snapshot_summary`.
- Show the agentic pipeline in the frontend after job completion.
- Keep existing module outputs compatible with current UI where possible.

Status: deterministic baseline implemented. Autonomous tool-calling agents, bounded LLM score adjustments, and historical outcome feedback remain later work.

### Phase 6: Document RAG Expansion

Goal: let SAGE add institutional knowledge without code changes while preserving deterministic, testable retrieval.

Deliverables:

- Add DB-backed RAG document source and chunk tables.
- Add admin-only source create/list/activate/deactivate APIs.
- Merge seeded JSON chunks with active admin-managed chunks in `RAGService`.
- Use DB-backed RAG in program-fit analysis.
- Add an admin knowledge panel.
- Add embeddings and pgvector semantic retrieval without creating a duplicate RAG module.
- Add PDF/DOCX upload/parsing without creating a duplicate ingestion module.
- Keep scheduled indexing as a later upgrade.

Status: DB-backed text-source baseline implemented; semantic embeddings, pgvector retrieval, embedding reindexing, and PDF/DOCX ingestion were added on 2026-05-23.

### Phase 7: Admission Intelligence

Goal: build the Admission Intelligence Command Center so counseling becomes more realistic, consistent, measurable, and institutionally useful.

Deliverables:

- Expectation Reality Check for configured branches and programs.
- Counselor Copilot conversation briefs.
- Admission Conversion Intelligence dashboard.
- Lost Admission Reason Analyzer.
- High-intent undecided student tracking.
- First 100-day roadmap after admission.

Status: deterministic baseline implemented. The current system derives admin-only admission metrics, high-intent and wrong-branch-risk lead cards, Counselor Copilot briefs, and lost-reason signals from existing twelfth-student profiles and latest program-fit analyses. CRM imports, counselor assignment, admission status tracking, outbound communication, and conversion funnel attribution remain later work.

### Phase 8: Placement Cell Intelligence

Goal: build the Placement Intelligence Command Center so the platform becomes operationally valuable to placement teams, faculty, and leadership.

Deliverables:

- Student Skill Evidence Ledger with skill-to-evidence mapping.
- Company-Specific Readiness Radar with readiness bands and missing-reason explanations.
- AI Placement War Room for upcoming company drives.
- Personal AI Faculty Advisor notes for mentee intervention planning.
- Outcome Simulation for student and cohort readiness improvements.
- Training ROI Engine with before/after readiness deltas.
- Cohort readiness heatmaps and high-risk intervention lists.
- Department and program dashboards.
- Placement strategy recommendations.

Status: deterministic baseline implemented. The current system derives admin-only placement metrics, Skill Evidence Ledger scores, Company-Specific Readiness Radar buckets, AI Placement War Room priority cards, Faculty Advisor notes, Outcome Simulation proxy signals, and Training ROI signals from existing college-student profiles and latest readiness records. Recruiter-drive scheduling, placed/not-placed outcomes, company JD imports, faculty assignment workflows, notifications, and historical training before/after measurement remain later work.

### Phase 9: Production Deployment

Goal: move from prototype deployment to maintainable launch deployment.

Deliverables:

- Containerized backend deployment.
- Google Cloud Run backend deployment path.
- Vercel frontend deployment notes.
- Supabase database and backup notes.
- AWS Bedrock LLM provider setup notes.
- Alembic migration runbook.
- Monitoring and logging plan.
- Error tracking plan.
- Environment variable checklist.

Status: launch-readiness artifacts implemented. The repository now includes a Cloud Run-compatible backend Dockerfile, dockerignore, Cloud Run env template, PowerShell and Cloud Shell deploy scripts, Cloud Run deployment and rollback runbook, Supabase migration guidance, Vercel `NEXT_PUBLIC_API_BASE_URL` guidance, and Bedrock production setup notes. Live deployment, real secret injection, Supabase production migration, and AWS model-access validation remain manual operational steps.

## Demo Strategy

The ceremony demo should tell one connected story:

1. A 12th student enters academic interests and gets a program or branch recommendation.
2. The Expectation Reality Check explains what the branch really requires.
3. The Counselor Copilot prepares a parent-friendly counseling brief.
4. The Admission Conversion dashboard shows high-intent undecided students and lost-admission reasons.
5. A current college student uploads or links a resume and receives employability insights.
6. The Skill Evidence Ledger shows which skills are verified and which are only claimed.
7. The Company-Specific Readiness Radar shows who is ready, almost ready, or blocked for a company drive.
8. The Outcome Simulation shows how one project, certification, or resume improvement changes readiness.
9. The AI Placement War Room turns those gaps into a placement-cell action plan.
10. The Training ROI Engine shows whether training improved readiness.
11. The AI pipeline view shows retrieval, scoring, verification, and final recommendation stages.

The demo should emphasize that this is not just a chatbot. It is an institutional decision system with agentic AI, RAG, deterministic scoring, and admin-ready analytics.

## Out Of Scope For First Production Pass

The first pass should not attempt:

- Full multi-tenant SaaS billing.
- Full admin CMS for every academic entity.
- Real-time integrations with every university system.
- Fully automated placement prediction from historical outcomes if historical data is not yet available.
- Student mobile app.
- Payment or monetization workflows.

These can be future roadmap items after the internal SAGE/SIRT platform is stable.

## Success Criteria

The design is successful if:

- The README and docs explain the product clearly to judges and engineers.
- The product story covers both admissions and placements.
- The pitch clearly showcases the Admission Intelligence Command Center as the counseling and conversion wow factor.
- The pitch clearly showcases the Placement Intelligence Command Center as the institutional wow factor.
- The architecture supports all SAGE schools and branches through configuration.
- AI behavior is presented as agentic, evidence-backed, and verified.
- The LLM layer targets AWS Bedrock native Amazon models instead of depending on an OpenAI-compatible production provider.
- Current working behavior is preserved during implementation.
- The backend tests and frontend build remain passing.
- The deployment path uses Google Cloud Run for backend launch-readiness and avoids dependence on a temporary Railway trial.
