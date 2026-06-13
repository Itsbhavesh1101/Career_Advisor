# Launch Acceptance Matrix

Last updated: 2026-05-23

This matrix tracks launch readiness from user point of view. It is intentionally stricter than unit tests: a feature is not considered launch-ready unless the route, user flow, backend contract, empty/error state, and visible copy match the intended student or admin journey.

## Current Gate

Status: backend deployed, admin RAG upload verified, the 12th-student browser path replayed through analysis, and an institutional-readiness wave is implemented locally pending deploy/live replay.

Fresh local evidence:

- Backend full regression: `uv run python -m pytest` from `backend` passed with `184 passed, 3 skipped`.
- Backend compile: `python -m compileall app tests main.py` from `backend` passed.
- Frontend production build: `npm run build` from `frontend` passed without the previous Next.js middleware deprecation warning.
- Frontend targeted RAG upload UI check passed before deploy; broader `npx biome check app components lib` still reports pre-existing formatting/import diagnostics.
- Institutional readiness local evidence: backend compile passed after schema/route/service changes; frontend `npm run build` passed; targeted Biome check passed for touched frontend files.

Fresh live evidence:

- Supabase/Postgres Alembic state was upgraded from `20260520_06` to `20260523_07`.
- Cloud Run `sage-career-backend` revision `sage-career-backend-00011-dsj` is serving 100% traffic.
- Cloud Run `/health` returned `200 {"status":"ok"}`.
- Vercel homepage returned `200`, and the live frontend bundle contains the new Cloud Run API base plus the admin RAG upload endpoint.
- Vercel-origin CORS preflight to `/api/v1/auth/me` returned `200` with credentials enabled.
- Live smoke user `sage-smoke-*` registered, logged in, created a 12th-student profile, and ran authenticated RAG search; RAG returned results for `placement` and `AI`.
- Production admin DOCX upload exposed and then verified a pgvector insert binding fix. The active Cloud Run revision is `sage-career-backend-00012-xvr`, serving 100% traffic.
- Admin account replay verified `/api/v1/auth/me` role `admin`, DOCX upload, embedding reindex, and RAG retrieval for the uploaded source.
- Browser admin dashboard replay verified the PDF/DOCX upload UI and the visible `Knowledge file uploaded.` notice.
- Browser 12th-student replay completed signup, profile creation, adaptive quiz, analysis finalization, and redirect to `/analysis/24`.

## Anonymous Visitor

| Scenario | Expected Behavior | Implementation Status |
| --- | --- | --- |
| `/` public homepage | Role-driven Admissions Showcase entry for 12th students, college students, and counselors/admins. | Updated in `frontend/app/page.tsx` with maroon/gold/teal visual system and role cards. |
| Logged-in user visits `/` | Student routes to `/dashboard`; admin routes to `/admin/dashboard`. | Updated in `AuthGate` and homepage session effect. |
| Protected route while logged out | Redirects to `/login` without exposing broken page state. | `AuthGate` handles client-side guard; Next proxy remains same-host cookie guard. |
| Login/signup public behavior | Authenticated users should not stay on auth pages. | Updated `AuthGate` public route redirect. |

## 12th Student Journey

| Scenario | Expected Behavior | Implementation Status |
| --- | --- | --- |
| Signup | User selects 12th student type and lands on dashboard/create-profile path. | Existing signup flow stores student type. |
| Create profile | Collects 12th percentage, subjects, interests, math strength, logical reasoning, and programming interest. Does not submit college-only values as fake defaults. | Updated `ProfileForm`; backend schema accepts null college-only fields and validates branch signals. |
| Adaptive quiz | Starts or resumes quiz, shows confidence/fallback states, and waits for analysis job before redirect. | Live browser replay completed quiz finalization and redirected to `/analysis/24`. |
| Branch/program guidance | Copy and outputs should focus on branch fit, program recommendations, expectation reality, and first-year roadmap. | Live browser replay reached `Branch & Program Guidance` on `/analysis/24`. |
| Dashboard | Shows branch guidance CTA or branch intelligence, not placement-only actions. | Existing dashboard hides training/internship links for 12th users. |
| Dashboard readiness summary | Shows profile completeness, quiz status, analysis status, admission-oriented summary, and next actions. | Added `StudentDashboardService`, `/api/v1/profiles/{profile_id}/dashboard`, and dashboard cards. |
| Edit profile | Preserves 12th flow and avoids reintroducing college-only defaults in the form payload. | Updated edit-page initial values and form payload. |

## College Student Journey

| Scenario | Expected Behavior | Implementation Status |
| --- | --- | --- |
| Create profile | Collects degree, specialization, CGPA, skills, target industry, projects, internships, and certifications. | Updated `ProfileForm` to expose projects/internships/certifications. |
| Adaptive quiz | Completes before analysis redirect and does not land on an empty page. | Existing quiz wait loop; needs browser replay. |
| Career analysis | Career recommendations, skill gaps, roadmap, salary, trends, chat, employability, company fit, role gaps, and placement risk are visible or generated with clear states. | Existing analysis page renders these modules; re-run now skips them for 12th users only. |
| Resume/training/internship | College-only routes remain linked in navbar/dashboard. | Existing navigation preserves these for college users. |
| Dashboard readiness summary | Shows profile completeness, quiz status, analysis status, resume status, placement-oriented summary, and next actions. | Added `StudentDashboardService`, `/api/v1/profiles/{profile_id}/dashboard`, and dashboard cards. |

## Admin/Counselor Journey

| Scenario | Expected Behavior | Implementation Status |
| --- | --- | --- |
| Admin dashboard | Shows admission intelligence, placement intelligence, RAG source management, and admin student list. | Existing `frontend/app/admin/dashboard/page.tsx` and panels present; needs browser replay. |
| System readiness | Shows LLM provider, embedding provider, vector-search state, failed jobs, failed embeddings, pending reviews, stale sources, and launch hints. | Added admin-only readiness endpoints and dashboard panel. |
| Student filters/export | Supports filtering by student type, readiness band, missing analysis, missing resume, and CSV export. | Added existing admin student endpoint query filters and `/api/v1/admin/students/export`. |
| Admission intelligence | Shows lead status, counselor briefs, lost-reason signals, and conversion metrics. | Existing API/panel present; docs should label as intelligence dashboard, not full CRM. |
| Placement intelligence and operations | Shows readiness metrics, company radar, evidence ledger, training ROI, faculty notes, company master records, placement opportunity board, eligible-student shortlists, application review lanes, next-step instructions, and CSV exports. | Existing intelligence API/panel plus placement opportunity/application/company-master module present; production row-level workflow still depends on institution data. |
| RAG sources | Admin can list/create/update text sources, upload PDF/DOCX sources, and approve/reject sources before retrieval. | Added RAG review lifecycle; new sources default to pending review and only active approved current sources are eligible for retrieval. |

## Failure Paths

| Scenario | Expected Behavior | Implementation Status |
| --- | --- | --- |
| Stale local profile ID | Clear invalid ID, fall back to latest valid profile, or send user to create-profile. | Added shared resolver in `frontend/lib/profile.ts`; dashboard/profile/create-profile now use it. |
| Missing analysis | Show generation CTA and progress/error state instead of empty charts. | Existing analysis page plus copy updates; quiz waits for job completion. |
| 12th profile submitted with college defaults | Backend rejects missing branch signals; frontend sends null for irrelevant college fields. | Regression covered by `test_student_profile_contracts.py`. |
| College profile missing placement fields | Backend rejects missing CGPA/degree/specialization/target industry. | Regression covered by `test_student_profile_contracts.py`. |
| Bedrock or async job slow/fails | UI should show progress, long-wait copy, and retryable error. | Existing job polling and gentle AI messages; live Bedrock failure path still needs production replay. |
| Pending or rejected RAG source | Source should remain visible to admins but not affect retrieval or student evidence. | Implemented review-gated RAG document retrieval. |

## Final Launch Blockers

- Optional cleanup of `sage-smoke-*` / `sage-e2e-*` test users and smoke-test RAG sources if production data hygiene requires removal.
- Deeper Bedrock log review for cost/latency/schema quality after the live analysis run.
- Open PR from `origin/dev` to `origin/main` if the launch branch policy requires main before final release.
- Apply Alembic revision `20260523_08` in production, then live-replay admin source upload -> approve -> reindex -> retrieval and student dashboard readiness.
