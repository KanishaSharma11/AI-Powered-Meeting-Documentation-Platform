"""
Shared pytest fixtures.

Tests run against a throwaway SQLite file, NOT your real Postgres
database — this makes the suite fast and safe to run repeatedly
without touching real data. The DATABASE_URL env var must be set
before app.core.config/app.main are imported anywhere, which is why
this happens at module load time, before the `from app...` imports
below.
"""

import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_pytest.db")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.meeting import Meeting
from app.models.transcript import TranscriptSegment
from app.models.extraction import ExtractedItem


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    """Create all tables once for the test session, drop + delete after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    try:
        os.remove("test_pytest.db")
    except OSError:
        pass


@pytest.fixture()
def client():
    """FastAPI TestClient — triggers startup/shutdown events."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def sample_transcript():
    return (
        "Sarah [00:00:05]: Let's discuss the login flow.\n"
        "Raj [00:00:12]: We need OTP login support.\n"
        "Sarah [00:00:20]: Agreed, OTP login is approved for launch.\n"
        "Sarah [00:00:28]: Raj, can you get the API contract to me by Friday?\n"
        "Raj [00:00:35]: Sure, I will send it by Friday.\n"
        "Sarah [00:00:42]: I'm worried the vendor API might not be ready in time.\n"
    )


@pytest.fixture()
def meeting_with_segments(db, client, sample_transcript):
    """
    Creates a meeting via the real upload endpoint (so normalization
    is exercised too), and returns (meeting_id, list_of_segment_ids).
    """
    res = client.post(
        "/api/transcripts/upload",
        json={"title": "Fixture Meeting", "raw_transcript": sample_transcript},
    )
    assert res.status_code == 200, res.text
    meeting_id = res.json()["id"]

    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == uuid.UUID(meeting_id))
        .order_by(TranscriptSegment.source_line_start)
        .all()
    )
    return meeting_id, segments


@pytest.fixture()
def project(client):
    res = client.post("/api/projects", json={"name": "Fixture Project", "description": "Test project"})
    assert res.status_code == 200, res.text
    return res.json()


@pytest.fixture()
def meeting_in_project(db, client, project):
    """A meeting that belongs to `project`, with normalized segments."""
    res = client.post(
        "/api/transcripts/upload",
        json={
            "title": "Project Meeting 1",
            "raw_transcript": "Sarah: OTP login is required.\nRaj: Agreed, approved.",
            "project_id": project["id"],
        },
    )
    assert res.status_code == 200, res.text
    meeting_id = res.json()["id"]

    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == uuid.UUID(meeting_id))
        .order_by(TranscriptSegment.source_line_start)
        .all()
    )
    return meeting_id, segments