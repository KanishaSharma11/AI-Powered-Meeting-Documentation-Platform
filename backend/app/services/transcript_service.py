from pathlib import Path

from app.services.normalization_service import (
    TranscriptNormalizationService,
)


class TranscriptService:
    """
    Handles transcript file reading and normalization.
    """

    def __init__(self):
        self.normalizer = (
            TranscriptNormalizationService()
        )

    def normalize_text(self, transcript: str):
        """
        Normalize raw transcript text.
        """

        return self.normalizer.normalize(
            transcript
        )

    def read_transcript_file(
        self,
        file_path: str,
    ) -> str:
        """
        Read a transcript file while preserving
        the original text.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Transcript file not found: {file_path}"
            )

        return path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    def normalize_file(
        self,
        file_path: str,
    ):
        """
        Read and normalize a transcript file.
        """

        transcript = (
            self.read_transcript_file(
                file_path
            )
        )

        return self.normalize_text(
            transcript
        )