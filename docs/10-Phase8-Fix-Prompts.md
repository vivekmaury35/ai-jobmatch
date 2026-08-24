# AI JobMatch — Phase 8 Fix Prompts (Post Phase-7 Review)

Run these in order in your existing Claude Code session — same project, same repo, no restart. This picks up after the Phase 7 review that found the skill-extraction bug (grouped/sentence-level "skills" instead of atomic terms) and the missing related-skill tier / sub-score display.

---

## Phase 8A — Diagnose the extraction bug (do this before fixing anything)
```
We found a bug: the JD/resume skill extraction is returning grouped
strings and full sentences as "skills" instead of individual skill
terms — for example "Frontend and backend development concepts" shows
up as a single missing skill, and "HTML, CSS, JavaScript, Python"
shows up as one matched-skill chip instead of four.

Before you fix anything, show me:
1. The current extraction prompt(s) sent to Gemini for JobProfile
   and ResumeProfile.
2. The Pydantic schema those responses are validated against.
3. A raw example of what Gemini actually returned for a real JD I'll
   paste in below.

Explain why you think the current prompt/schema is allowing this to
happen, before writing any fix.
```
**Paste in the sample JD from your test** so it reproduces the exact bug you saw. **Read:** Learning Guide → Phase 3 section (structured extraction) as a refresher before this one.

---

## Phase 8B — Fix skill extraction
```
Fix the extraction so required_skills, preferred_skills, and resume
skills are always individual atomic terms — never comma-grouped
strings, never full sentences. Specifically:
1. Update the extraction prompt(s) to explicitly instruct: "each skill
   must be a single technology, tool, or concept, 1-3 words max — do
   not group multiple skills into one string, do not extract full
   sentences or requirement clauses as skills."
2. Add a post-extraction validation step: any extracted "skill" string
   longer than ~4 words or containing a comma should be flagged and
   either split or rejected, not passed downstream as-is.
3. Re-run extraction on the same JD I gave you in Phase 8A and show me
   the before/after output side by side.
```
**Verify:** re-run the exact same JD+resume through the full app; confirm skill chips are now atomic (e.g. "JavaScript" and "Python" as separate chips, not one grouped string), and no full sentences appear as "missing skills."
**Git checkpoint:** `fix: atomic skill extraction, reject grouped/sentence-level skills`

---

## Phase 8C — Surface the related-skill tier + sub-score cards
```
Two UI gaps to close, per 06-UI-UX.md:

1. Check whether related_skills (the amber "semantic similarity but
   not exact" tier) is actually being computed by the matching engine
   but just not rendered — show me where in the code this data exists
   or doesn't. If it's missing entirely, implement it per FR-14 in
   02-SRS.md. If it exists, add it to the results page as a third,
   amber-colored chip group with a "related to X" tooltip.

2. Add the SubScoreCard row from 06-UI-UX.md section 2.2 — currently
   the sub-scores (skill/semantic/experience/education/project
   evidence) only appear inside the explanation paragraph. Show them
   as 3-5 individual stat cards above or below the main score, the way
   the spec describes.

Explain to me which of these two was already computed on the backend
and just not displayed, versus which required new backend logic.
```
**Verify:** results page now shows three skill-chip colors (green/red/amber) and a visible row of sub-score numbers, not just prose.
**Read:** Learning Guide → Phase 5 section (the tiering logic) as a refresher.
**Git checkpoint:** `feat: surface related-skill tier and sub-score cards in results UI`

---

## Phase 8D — Fix history display
```
The History page currently shows the analysis ID (e.g. "2416aafb")
instead of the job title. Fix it to display the extracted job title
(from JobProfile.title) next to the score and date, per
06-UI-UX.md section 2.3. If job title isn't currently being stored
or returned by the analyses list endpoint, fix that first.
```
**Verify:** History page shows readable job titles, not raw IDs.
**Git checkpoint:** `fix: display job title instead of analysis ID in history`

---

## Phase 8E — Testing & Hardening (now meaningful, since the bug is fixed)
```
Now that skill extraction is fixed, run the full testing pass:
1. Pytest coverage for the scoring engine (pure functions, no AI
   calls needed).
2. API endpoint tests — happy path and key error paths (bad PDF, JD
   too short, AI provider timeout).
3. Manually re-test with the same resume against 3 different real JDs
   of varying seniority, and confirm skill chips stay atomic and
   scores are reproducible (same resume+JD run twice = same score).
4. Grep the codebase for any "ATS certified" language per NFR-8 —
   confirm none exists.
5. Confirm no AI provider key is present anywhere in frontend code or
   NEXT_PUBLIC_* env vars per NFR-4.

Show me the test output and explain what each test is actually
checking.
```
**Read:** Learning Guide → Phase 8 section.
**Git checkpoint:** `test: scoring engine and API coverage after extraction fix`

---

## Phase 9 — Deployment *(unchanged from the original roadmap — run as originally written)*
```
Phase 9: Deployment. Walk me through deploying backend to
Render/Railway, frontend to Vercel, database to Neon or Supabase.
Tell me exactly which env vars to set on each platform, in what order
to deploy so migrations run correctly, and what to click in each
dashboard — I haven't used any of these platforms before.
```
**You do manually:** create Render/Railway and Neon/Supabase accounts; click through their dashboards as instructed.
**Read:** Learning Guide → Phase 9 section.
**Git checkpoint:** `chore: deployment configuration (Phase 9)`

---

## Phase 10 — Documentation *(revised — includes the honest fix narrative)*
```
Phase 10: Documentation. Write README.md — what it does, the
architecture diagram from 03-System-Architecture.md, tech stack, how
to run locally, and a "key engineering decisions" section. Include a
short, honest note under "what I'd improve further" about the skill-
extraction bug you found and fixed in Phase 8 — how you diagnosed it,
what the root cause was, and how you fixed it. This is a real
engineering story worth telling, not something to hide.
```
**Read:** Learning Guide → Phase 10 section.
**Git checkpoint:** `docs: README and project documentation (Phase 10)`

---

## Optional — Priority 4 polish (only after everything above is done)
```
Now that the core fixes are in, pick one small polish item at a time
from: score display precision/formatting, evidence drill-down per
skill (click a chip to see where it was found in the resume), or an
ATS-style keyword coverage panel. Tell me which is lowest-effort
given the current codebase before we pick one.
```

---

## Standing rule, same as before
If Claude Code drifts into Tier 2/3 features (radar charts, recruiter summaries, DOCX support) before 8A–8E are done, redirect it: *"That's later — stay inside the current phase."* For 8A specifically: don't let it skip straight to "fixed it" without actually showing you the current prompt/schema and the before/after — that diagnostic step is where you actually learn what went wrong, not just that it's now different.
