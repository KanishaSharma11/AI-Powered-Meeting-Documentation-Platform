from app.services.normalization import normalize_transcript
import pytest

# ---------- Unit tests: normalization ----------

def test_normalize_parses_speaker_and_timestamp():
    raw = "Sarah [00:00:05]: Let's discuss the login flow."
    result = normalize_transcript(raw)

    assert len(result.segments) == 1
    seg = result.segments[0]
    assert seg.segment_id == "SEG-0001"
    assert seg.speaker == "Sarah"
    assert seg.timestamp_start == "00:00:05"
    assert seg.text == "Let's discuss the login flow."


def test_normalize_handles_no_timestamp():
    raw = "Raj: We need OTP login support."
    result = normalize_transcript(raw)

    seg = result.segments[0]
    assert seg.speaker == "Raj"
    assert seg.timestamp_start is None
    assert seg.text == "We need OTP login support."


def test_normalize_handles_unattributed_line():
    raw = "This line has no speaker prefix at all"
    result = normalize_transcript(raw)

    seg = result.segments[0]
    assert seg.speaker is None
    assert seg.text == "This line has no speaker prefix at all"


def test_normalize_skips_blank_lines():
    raw = "Sarah: Hello.\n\n\nRaj: Hi there."
    result = normalize_transcript(raw)

    assert len(result.segments) == 2
    assert result.segments[0].segment_id == "SEG-0001"
    assert result.segments[1].segment_id == "SEG-0002"


# ---------- Integration tests: /api/transcripts ----------

def test_upload_transcript_creates_meeting(client, sample_transcript):
    res = client.post(
        "/api/transcripts/upload",
        json={
            "title": "Design Review",
            "meeting_date": "2026-08-20",
            "raw_transcript": sample_transcript,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["title"] == "Design Review"
    assert body["meeting_date"] == "2026-08-20"
    assert body["source_type"] == "official_transcript"
    assert body["segment_count"] == 6


def test_upload_empty_transcript_returns_400(client):
    res = client.post(
        "/api/transcripts/upload",
        json={"title": "Empty Meeting", "raw_transcript": "   "},
    )
    assert res.status_code == 400


def test_get_segments_for_uploaded_meeting(client, meeting_with_segments):
    meeting_id, _ = meeting_with_segments
    res = client.get(f"/api/transcripts/{meeting_id}/segments")
    assert res.status_code == 200
    segments = res.json()
    assert len(segments) == 6
    assert segments[0]["segment_id"] == "SEG-0001"
    assert segments[0]["speaker"] == "Sarah"


def test_get_segments_for_unknown_meeting_returns_404(client):
    res = client.get("/api/transcripts/00000000-0000-0000-0000-000000000000/segments")
    assert res.status_code == 404


def test_list_meetings_includes_uploaded_meeting(client, meeting_with_segments):
    meeting_id, _ = meeting_with_segments
    res = client.get("/api/transcripts")
    assert res.status_code == 200
    ids = [m["id"] for m in res.json()]
    assert meeting_id in ids