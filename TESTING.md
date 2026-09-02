# Testing the Backend

There are two layers of testing here — use both.

## 1. Automated tests (`pytest`) — run these first, every time

These run against a throwaway SQLite file and **mock the AI agents**,
so they don't need Postgres or Ollama running. They check your actual
logic: normalization, evidence resolution, confidence scoring, the
review state machine, and MOM generation.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # if not already set up
pip install -r requirements-dev.txt
pytest -v
```

Expected: **26 passed**. If anything fails after you've made changes,
that's a real regression — fix it before moving on to manual testing.

What's covered (see `tests/`):

| File | Covers |
|---|---|
| `test_transcript.py` | Normalization edge cases (timestamps, no speaker, blank lines) + upload/list/get-segments endpoints |
| `test_review_workflow.py` | Accept/edit/reject state transitions, validation, low-confidence flagging |
| `test_mom_generation.py` | MOM only includes accepted/edited items, real `.docx` bytes are produced |
| `test_extraction_service.py` | Evidence resolution (segment_id → real speaker/timestamp/text from the DB, not the LLM), confidence math, re-running extraction replaces rather than duplicates |

Run a single file or test while iterating:
```bash
pytest tests/test_review_workflow.py -v
pytest tests/test_review_workflow.py::test_edit_item_success -v
```

## 2. Manual testing against real Postgres + Ollama

This is what actually proves the LLM extraction quality — pytest
deliberately mocks that part out.

### Setup

```bash
# Postgres running and reachable, backend/.env pointing at it
# (copy backend/.env.example and fill in real values)

ollama serve
ollama pull qwen3:8b     # or whatever OLLAMA_MODEL is set to

cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Confirm tables got created:
```bash
psql "$DATABASE_URL" -c "\dt"
# expect: meetings, transcript_segments, extracted_items
```

### Walkthrough via curl

**Health check:**
```bash
curl -s http://localhost:8000/api/health
```

**Upload a transcript:**
```bash
curl -s -X POST http://localhost:8000/api/transcripts/upload \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Requirements Workshop",
    "meeting_date": "2026-08-20",
    "raw_transcript": "Sarah [00:00:05]: Let'"'"'s discuss the login flow.\nRaj [00:00:12]: We need OTP login support.\nSarah [00:00:20]: Agreed, OTP login is approved for launch.\nSarah [00:00:28]: Raj, can you get the API contract to me by Friday?\nRaj [00:00:35]: Sure, I will send it by Friday.\nSarah [00:00:42]: I am worried the vendor API might not be ready in time."
  }'
```
Save the returned `"id"` — you'll need it below. Call it `MEETING_ID`.

**Check the normalized segments look right:**
```bash
curl -s http://localhost:8000/api/transcripts/$MEETING_ID/segments | python3 -m json.tool
```
Confirm: 6 segments, speakers `Sarah`/`Raj` correctly attributed,
timestamps parsed.

**Run extraction (this is the real LLM call — watch for it to take a
few seconds depending on your model/hardware):**
```bash
curl -s -X POST http://localhost:8000/api/meetings/$MEETING_ID/extract | python3 -m json.tool
```
This is the important one to eyeball carefully. Check:
- Does `requirements_count` show 1 (OTP login)?
- Does `decisions_count` show 1 (OTP login approved)?
- Does `action_items_count` show 1, with `owner: "Raj"` and
  `due_date` mentioning Friday?
- Does `risks_count` show 1 (vendor API concern)?
- For every item: does `segment_id` point at a real segment, and do
  `evidence_speaker`/`evidence_timestamp`/`evidence_text` match what's
  actually in that segment? (This is the "evidence-backed" claim from
  Section 1.3 — it should never be empty or mismatched.)
- Are `extraction_confidence` values reasonable (not all exactly 1.0 —
  that usually means the model isn't actually reasoning about
  confidence)?

If items look wrong (missed something obvious, hallucinated an owner,
wrong segment_id), that's a prompt-tuning problem in
`app/ai/prompts/*.py`, not a wiring problem — the tests already prove
the wiring works.

**Review the items — grab an item id from the previous response:**
```bash
curl -s -X PATCH http://localhost:8000/api/extractions/$ITEM_ID \
  -H "Content-Type: application/json" \
  -d '{"action": "accept"}'

curl -s -X PATCH http://localhost:8000/api/extractions/$ITEM_ID \
  -H "Content-Type: application/json" \
  -d '{"action": "edit", "edited_text": "The system must support OTP-based login."}'
```

**Preview the MOM (JSON, only accepted/edited items):**
```bash
curl -s http://localhost:8000/api/meetings/$MEETING_ID/mom/preview | python3 -m json.tool
```

**Download the actual .docx:**
```bash
curl -s http://localhost:8000/api/meetings/$MEETING_ID/mom/download -o mom.docx
open mom.docx   # or: xdg-open mom.docx / start mom.docx
```
Open it and confirm formatting looks right and only reviewed items
appear.

### Or: use the interactive API docs instead of curl

FastAPI gives you a full interactive UI for free — often easier than
curl for manual testing:

```
http://localhost:8000/docs
```

Every endpoint above can be called directly from there with a form UI,
including seeing the exact request/response schemas.

## Things worth deliberately testing (edge cases)

- Upload a transcript with **no timestamps at all** — does normalization
  still work? (It should — see `test_normalize_handles_no_timestamp`.)
- Upload a transcript where **every line is unattributed** (no
  `Speaker:` prefix) — extraction should still run, just with
  `speaker: "Unknown"` everywhere.
- Run extraction **twice** on the same meeting — second run should
  replace items, not duplicate them.
- Try downloading a MOM **before running extraction** — should 400.
- Try downloading a MOM where **everything was rejected** — should 400.
- Reject an item, then re-check `/mom/preview` — it should NOT appear.
