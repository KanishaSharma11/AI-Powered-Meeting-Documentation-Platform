from pathlib import Path

from app.services.transcript_service import (
    TranscriptService,
)


def test_coastal_meeting_normalization():

    transcript_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "samples"
        / "coastal_meeting.txt"
    )

    service = TranscriptService()

    normalized = service.normalize_file(
        str(transcript_path)
    )

    assert normalized.original_text

    assert len(normalized.segments) > 0

    print(
        "\n"
        f"Source format: "
        f"{normalized.source_format}"
    )

    print(
        "\n"
        f"Total segments: "
        f"{len(normalized.segments)}"
    )

    print("\nFirst 20 normalized segments:")

    for segment in normalized.segments[:20]:

        print(
            f"\n{segment.segment_id}"
            f"\nSpeaker: {segment.speaker}"
            f"\nTimestamp: "
            f"{segment.timestamp_start}"
            f"\nLines: "
            f"{segment.source_line_start}-"
            f"{segment.source_line_end}"
            f"\nText: {segment.text}"
        )


def test_transcript_service_import():

    service = TranscriptService()

    assert service is not None