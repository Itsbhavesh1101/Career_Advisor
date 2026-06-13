# Placement TnP Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a launch-useful placement opportunity and student application lifecycle without building a full ATS or duplicating the existing admin dashboard.

**Architecture:** Add two focused backend tables, `placement_opportunities` and `placement_applications`, with a service that handles admin CRUD, student discovery, student apply/status updates, and CSV export. Expose these through new `/api/v1/placement-opportunities` routes, then integrate the existing admin dashboard and internship/student readiness pages through the existing frontend API client.

**Tech Stack:** FastAPI, SQLAlchemy ORM, Alembic, Pydantic v2, Next.js app router, TypeScript, existing white/orange/black UI primitives.

---

### Task 1: Backend Contract Tests

**Files:**
- Create: `backend/tests/test_placement_opportunity_routes.py`
- Create: `backend/tests/test_placement_opportunity_service.py`

- [ ] Add route tests proving admins can create/list/update/export opportunities and students can list/apply.
- [ ] Add service tests proving matching uses active opportunities, student skills, student type, and duplicate applications are rejected.
- [ ] Run `uv run python -m pytest tests/test_placement_opportunity_routes.py tests/test_placement_opportunity_service.py -q` and confirm the tests fail because the module/routes do not exist yet.

### Task 2: Backend Implementation

**Files:**
- Create: `backend/app/models/placement_opportunity.py`
- Create: `backend/app/schemas/placement_opportunity.py`
- Create: `backend/app/services/placement_opportunity_service.py`
- Create: `backend/app/api/routes/placement_opportunities.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/api/router.py`
- Create: `backend/alembic/versions/20260525_11_add_placement_opportunities.py`

- [ ] Add SQLAlchemy models for opportunities and applications.
- [ ] Add Pydantic schemas for admin create/update/read, student match read, application read/update, and list responses.
- [ ] Add service methods for admin CRUD/list/export, student list, student apply, student applications, and admin application status updates.
- [ ] Register the new router under `/api/v1/placement-opportunities`.
- [ ] Run the focused backend tests and confirm they pass.

### Task 3: Frontend API + Admin UI

**Files:**
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/admin/dashboard/page.tsx`

- [ ] Add TypeScript types and API helpers for opportunities, applications, apply, status update, and CSV export.
- [ ] Add a compact `Placement Opportunities` admin panel inside the existing admin dashboard, not a new route.
- [ ] Show opportunity status, deadline, applicant counts, and application status controls.

### Task 4: Student Opportunity UI

**Files:**
- Modify: `frontend/app/internship/page.tsx`
- Optionally modify: `frontend/app/dashboard/page.tsx`

- [ ] Show matched active opportunities in the existing internship readiness loop.
- [ ] Add an apply/mark-interest action that creates the placement application.
- [ ] Keep empty/error states clear and do not expose admin-only weak-skill cohort signals to students.

### Task 5: Verification, Docs, Ship

**Files:**
- Modify: `MEMORY.md`

- [ ] Run focused backend tests.
- [ ] Run backend compileall.
- [ ] Run targeted frontend Biome.
- [ ] Run frontend build.
- [ ] Run `git diff --check`.
- [ ] Smoke local UI where practical.
- [ ] Update `MEMORY.md`, commit to `dev`, push, open PR to `main`, merge after checks, and live smoke Vercel/Cloud Run if backend migration/deploy is required.
