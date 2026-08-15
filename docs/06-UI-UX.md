# AI JobMatch — UI/UX Specification

## 1. Design Direction
Dark, technical, product-analytics aesthetic (matches the original portfolio screenshot). Palette: near-black background, dark gray surfaces, white text, blue as primary accent, green for positive/match signals, red/amber for gaps. Avoid generic "AI startup gradient" clichés — keep it sharp and data-dense, closer to a developer tool than a marketing site.

## 2. Pages (MVP)

### 2.1 `/` — Analyze
- Two-panel input: resume upload (drag/drop PDF) on the left, JD paste textarea on the right.
- Primary CTA: "Analyze Match" — disabled until both inputs are present.
- On submit: replace the panel with a step-by-step progress indicator (see §4), then route to `/results/[id]` on completion.

### 2.2 `/results/[id]` — Analysis Result
Top to bottom:
1. Header: job title + overall score as a large number with a qualitative label (e.g. "82% — Strong Match").
2. Sub-score row: 3–5 small stat cards (Skills, Semantic, Experience, Education).
3. Matching Skills (green chips) / Missing Skills (red chips) / Related Skills (amber chips, with "related to X" tooltip).
4. Explanation panel: 2–4 sentence plain-language summary of the score.
5. Recommendations list: numbered, concrete, evidence-based suggestions.
6. "Save to history" state indicator (auto-saved is fine — just show a subtle confirmation).

### 2.3 `/history` — Past Analyses
- Simple table/list: job title, score, date, link to `/results/[id]`.
- Empty state: friendly prompt back to `/`.

## 3. Components (MVP)
```
components/
├── ResumeUpload.tsx        # drag/drop + file validation feedback
├── JobDescriptionInput.tsx # textarea + word-count validation
├── AnalysisProgress.tsx    # step list, see §4
├── ScoreHeader.tsx         # big score + label
├── SubScoreCard.tsx        # one stat card, reused 3-5x
├── SkillChipList.tsx       # matched/missing/related, color-coded
├── ExplanationPanel.tsx
├── RecommendationList.tsx
└── HistoryTable.tsx
```

## 4. Analysis Progress Feedback
While `/api/analyze` runs, show real sequential status text (not fake — tie to actual backend steps if using SSE/polling; otherwise a reasonable fixed sequence is acceptable for MVP):
```
✓ Resume uploaded
✓ Extracting resume content
✓ Analyzing job description
✓ Matching skills
✓ Computing similarity
✓ Generating explanation
```
Keep this honest — don't fabricate steps the backend isn't actually doing.

## 5. States to Design For
- Empty (no resume/JD yet) — CTA disabled, helper text visible.
- Loading (analysis in progress) — progress indicator, CTA replaced/disabled.
- Error (bad PDF, JD too short, AI provider failure) — inline, specific error message near the relevant input, not a generic toast only.
- Success (result rendered).
- Empty history (no past analyses yet).

## 6. Accessibility & Responsiveness
- All interactive elements keyboard-navigable (upload dropzone must have a functional file-picker fallback).
- Color is never the only signal for match/missing/related — use icons or text labels alongside color chips.
- Layout must work down to a single-column mobile view (results page in particular — stack sub-score cards vertically below ~640px).

## 7. Phase 2 UI Additions (not MVP)
- Radar chart (sub-scores) — Recharts.
- Skill Gap Matrix table (skill / candidate level / required / match tier).
- Evidence drill-down (click a skill chip to see exactly where it was found).
- Recruiter Summary card (separate shareable view).
- Resume Quality Score panel (independent of JD).

## 8. Copy/Tone Guidelines
- Never claim "ATS certified" or "guaranteed to pass ATS" — use "ATS-style keyword analysis."
- Explanation and recommendation text should read like a knowledgeable peer reviewing the resume, not marketing copy.
- Error messages should say what happened and what to do next, not just "Something went wrong."
