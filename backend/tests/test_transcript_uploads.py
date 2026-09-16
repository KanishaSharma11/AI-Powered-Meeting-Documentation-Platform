import io

from docx import Document
from fpdf import FPDF


def _sample_pdf_bytes() -> bytes:
    # ln=1 (not new_x/new_y) for compatibility across fpdf2 versions --
    # deprecated on newer releases but still functional; new_x/new_y
    # only exists on fpdf2 >= 2.7.4.
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in ["Sarah: Lets discuss the login flow.", "Raj: We need OTP login support."]:
        pdf.cell(0, 10, line, ln=1)
    return _pdf_output_to_bytes(pdf)


def _pdf_output_to_bytes(pdf) -> bytes:
    # Older fpdf2 (and legacy fpdf) return str from .output(); newer
    # versions return bytearray. Handle both.
    output = pdf.output()
    if isinstance(output, str):
        return output.encode("latin-1")
    return bytes(output)

def _sample_docx_bytes() -> bytes:
    doc = Document()
    doc.add_paragraph("Sarah: Lets discuss the login flow.")
    doc.add_paragraph("Raj: We need OTP login support.")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------- PDF/DOCX file upload ----------

def test_upload_pdf_transcript(client):
    res = client.post(
        "/api/transcripts/upload-file",
        data={"title": "PDF Meeting"},
        files={"file": ("transcript.pdf", _sample_pdf_bytes(), "application/pdf")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["segment_count"] == 2
    assert body["source_type"] == "official_transcript"


def test_upload_docx_transcript(client):
    res = client.post(
        "/api/transcripts/upload-file",
        data={"title": "DOCX Meeting"},
        files={"file": ("transcript.docx", _sample_docx_bytes(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert res.status_code == 200, res.text
    assert res.json()["segment_count"] == 2


def test_upload_file_rejects_unsupported_extension(client):
    res = client.post(
        "/api/transcripts/upload-file",
        data={"title": "Bad file"},
        files={"file": ("transcript.doc", b"legacy binary format", "application/msword")},
    )
    assert res.status_code == 400


def test_upload_file_rejects_empty_pdf_text(client):
    pdf = FPDF()
    pdf.add_page()  # blank page, no text at all
    res = client.post(
        "/api/transcripts/upload-file",
        data={"title": "Blank PDF"},
        files={"file": ("blank.pdf", _pdf_output_to_bytes(pdf), "application/pdf")},
    )
    assert res.status_code == 400


def test_upload_file_with_unknown_project_returns_404(client):
    res = client.post(
        "/api/transcripts/upload-file",
        data={"title": "Orphan", "project_id": "00000000-0000-0000-0000-000000000000"},
        files={"file": ("transcript.pdf", _sample_pdf_bytes(), "application/pdf")},
    )
    assert res.status_code == 404


def test_upload_file_links_to_project(client):
    project_res = client.post("/api/projects", json={"name": "File Upload Project"})
    project_id = project_res.json()["id"]

    res = client.post(
        "/api/transcripts/upload-file",
        data={"title": "Linked", "project_id": project_id},
        files={"file": ("transcript.pdf", _sample_pdf_bytes(), "application/pdf")},
    )
    assert res.status_code == 200
    assert res.json()["project_id"] == project_id


# ---------- Audio upload (Stage 5) ----------

def test_upload_audio_transcribes_and_persists(client, monkeypatch):
    import app.services.audio_transcription_service as ats

    class FakeSegment:
        def __init__(self, start, end, text):
            self.start, self.end, self.text = start, end, text

    class FakeWhisperModel:
        def __init__(self, *a, **kw):
            pass
        def transcribe(self, path, vad_filter=True):
            return iter([
                FakeSegment(0.0, 3.0, "Lets discuss the login flow."),
                FakeSegment(3.0, 6.0, "We need OTP login support."),
            ]), None

    monkeypatch.setattr(ats, "WhisperModel", FakeWhisperModel)

    res = client.post(
        "/api/transcripts/upload-audio",
        data={"title": "Audio Meeting", "source_type": "meeting_bot_audio"},
        files={"file": ("meeting.wav", b"fake audio bytes", "audio/wav")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["segment_count"] == 2
    assert body["source_type"] == "meeting_bot_audio"


def test_upload_audio_rejects_invalid_source_type(client):
    res = client.post(
        "/api/transcripts/upload-audio",
        data={"title": "Bad source", "source_type": "official_transcript"},
        files={"file": ("meeting.wav", b"fake audio bytes", "audio/wav")},
    )
    assert res.status_code == 400


def test_upload_audio_with_no_speech_returns_400(client, monkeypatch):
    import app.services.audio_transcription_service as ats

    class FakeWhisperModelSilent:
        def __init__(self, *a, **kw):
            pass
        def transcribe(self, path, vad_filter=True):
            return iter([]), None  # nothing detected

    monkeypatch.setattr(ats, "WhisperModel", FakeWhisperModelSilent)

    res = client.post(
        "/api/transcripts/upload-audio",
        data={"title": "Silent", "source_type": "screen_share_audio"},
        files={"file": ("silence.wav", b"fake audio bytes", "audio/wav")},
    )
    assert res.status_code == 400


def test_segments_have_no_speaker_without_diarization(client, db, monkeypatch):
    import app.services.audio_transcription_service as ats
    from app.models.transcript import TranscriptSegment
    import uuid

    class FakeSegment:
        def __init__(self, start, end, text):
            self.start, self.end, self.text = start, end, text

    class FakeWhisperModel:
        def __init__(self, *a, **kw):
            pass
        def transcribe(self, path, vad_filter=True):
            return iter([FakeSegment(0.0, 2.0, "Some spoken text.")]), None

    monkeypatch.setattr(ats, "WhisperModel", FakeWhisperModel)

    res = client.post(
        "/api/transcripts/upload-audio",
        data={"title": "No diarization", "source_type": "meeting_bot_audio"},
        files={"file": ("meeting.wav", b"fake", "audio/wav")},
    )
    meeting_id = res.json()["id"]
    seg = db.query(TranscriptSegment).filter_by(meeting_id=uuid.UUID(meeting_id)).first()
    assert seg.speaker == "Unknown"  # honestly reflects no diarization performed