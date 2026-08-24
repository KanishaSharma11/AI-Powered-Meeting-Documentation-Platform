import re

from app.schemas.transcript import (
    NormalizedTranscript,
    TranscriptSegment,
)


class TranscriptNormalizationService:
    """
    Normalizes different transcript formats into a common
    internal representation.

    The original transcript is always preserved.

    Supported formats include:

        Shyam Jagannathan   11:47
        Ravi Kumar(SS)      11:49
        Sarah               01:10:15

        [00:10:15] Sarah: Hello everyone.
        Sarah (00:10:15): Hello everyone.
        Sarah(00:10:15): Hello everyone.
        00:10:15 - Sarah: Hello everyone.
        Sarah: Hello everyone.

    Continuation lines are attached to the preceding speaker
    segment.
    """

    # ---------------------------------------------------------
    # Common timestamp pattern
    #
    # Supports:
    #
    # 10:15
    # 00:10:15
    # 1:10:15
    # ---------------------------------------------------------

    TIMESTAMP_PATTERN = (
        r"\d{1,2}:\d{2}(?::\d{2})?"
    )

    # ---------------------------------------------------------
    # Speaker + timestamp
    #
    # Examples:
    #
    # Shyam Jagannathan   11:47
    # Ravi Kumar(SS)      11:49
    # Sarah               01:10:15
    #
    # IMPORTANT:
    # This pattern is checked BEFORE the more general
    # speaker/timestamp/text pattern.
    # ---------------------------------------------------------

    SPEAKER_TIMESTAMP_PATTERN = re.compile(
        r"^\s*"
        r"(?P<speaker>.+?)"
        r"\s+"
        rf"(?P<timestamp>{TIMESTAMP_PATTERN})"
        r"\s*$"
    )

    # ---------------------------------------------------------
    # Timestamp + speaker + text
    #
    # Examples:
    #
    # [00:10:15] Sarah: Hello everyone.
    # 00:10:15 Sarah: Hello everyone.
    # ---------------------------------------------------------

    TIMESTAMP_SPEAKER_PATTERN = re.compile(
        r"^\s*\[?"
        rf"(?P<timestamp>{TIMESTAMP_PATTERN})"
        r"\]?"
        r"\s+"
        r"(?P<speaker>.+?)"
        r"\s*:\s*"
        r"(?P<text>.*)$"
    )

    # ---------------------------------------------------------
    # Speaker + timestamp + text
    #
    # Examples:
    #
    # Sarah (00:10:15): Hello everyone.
    # Sarah(00:10:15): Hello everyone.
    # Sarah 00:10:15: Hello everyone.
    # ---------------------------------------------------------

    SPEAKER_TIMESTAMP_TEXT_PATTERN = re.compile(
        r"^\s*"
        r"(?P<speaker>.+?)"
        r"\s+"
        r"\(?"
        rf"(?P<timestamp>{TIMESTAMP_PATTERN})"
        r"\)?"
        r"\s*:?\s*"
        r"(?P<text>.+)$"
    )

    # ---------------------------------------------------------
    # Speaker + colon + text
    #
    # Example:
    #
    # Sarah: Hello everyone.
    # ---------------------------------------------------------

    SPEAKER_COLON_PATTERN = re.compile(
        r"^\s*"
        r"(?P<speaker>[^:\n]{1,100})"
        r"\s*:\s*"
        r"(?P<text>.+)$"
    )

    # ---------------------------------------------------------
    # Timestamp + dash + speaker + text
    #
    # Examples:
    #
    # 00:10:15 - Sarah: Hello everyone.
    # 00:10:15 – Sarah: Hello everyone.
    # 00:10:15 — Sarah: Hello everyone.
    # ---------------------------------------------------------

    TIMESTAMP_DASH_SPEAKER_PATTERN = re.compile(
        r"^\s*\[?"
        rf"(?P<timestamp>{TIMESTAMP_PATTERN})"
        r"\]?"
        r"\s*[-–—]\s*"
        r"(?P<speaker>[^:\n]{1,100})"
        r"\s*:?\s*"
        r"(?P<text>.*)$"
    )

    def normalize(
        self,
        transcript: str,
    ) -> NormalizedTranscript:
        """
        Convert raw transcript text into normalized
        speaker segments.

        The original transcript is preserved exactly.

        Each normalized segment receives a generated ID:

            SEG-0001
            SEG-0002
            SEG-0003
            ...

        Speaker and timestamp information comes from the
        transcript rather than from the LLM.
        """

        # -----------------------------------------------------
        # Validate input
        # -----------------------------------------------------

        if not transcript or not transcript.strip():
            raise ValueError(
                "Transcript cannot be empty."
            )

        original_text = transcript

        # splitlines() preserves logical source-line ordering.
        lines = transcript.splitlines()

        segments = []

        current_segment = None

        detected_formats = set()

        # -----------------------------------------------------
        # Parse transcript line-by-line
        # -----------------------------------------------------

        for line_number, raw_line in enumerate(
            lines,
            start=1,
        ):

            line = raw_line.strip()

            # Ignore completely blank lines.
            #
            # IMPORTANT:
            # We do NOT update source_line_end for blank lines.
            # source_line_end therefore refers to the last
            # actual transcript line containing content.
            if not line:
                continue

            parsed = self._parse_line(line)

            # -------------------------------------------------
            # New speaker segment
            # -------------------------------------------------

            if parsed:

                # Save previous segment first.
                if current_segment is not None:
                    segments.append(
                        current_segment
                    )

                current_segment = {
                    "speaker": parsed.get(
                        "speaker"
                    ),
                    "timestamp_start": parsed.get(
                        "timestamp"
                    ),
                    "timestamp_end": None,
                    "text": parsed.get(
                        "text",
                        "",
                    ),
                    "source_line_start": line_number,
                    "source_line_end": line_number,
                }

                detected_formats.add(
                    parsed.get(
                        "format",
                        "unknown",
                    )
                )

            # -------------------------------------------------
            # Continuation line
            # -------------------------------------------------

            else:

                if current_segment is not None:

                    current_text = current_segment[
                        "text"
                    ]

                    if current_text:

                        current_segment["text"] = (
                            current_text
                            + " "
                            + line
                        )

                    else:

                        current_segment["text"] = line

                    # Update only when an actual content line
                    # is added.
                    current_segment[
                        "source_line_end"
                    ] = line_number

                # -------------------------------------------------
                # Text appearing before a recognizable speaker
                # -------------------------------------------------

                else:

                    current_segment = {
                        "speaker": None,
                        "timestamp_start": None,
                        "timestamp_end": None,
                        "text": line,
                        "source_line_start": line_number,
                        "source_line_end": line_number,
                    }

                    detected_formats.add(
                        "unidentified"
                    )

        # -----------------------------------------------------
        # Add final segment
        # -----------------------------------------------------

        if current_segment is not None:
            segments.append(current_segment)

        # -----------------------------------------------------
        # Build validated Pydantic segments
        # -----------------------------------------------------

        normalized_segments = []

        segment_counter = 1

        for segment in segments:

            text = self._clean_text(
                segment["text"]
            )

            # Ignore segments that contain no actual text.
            #
            # This prevents a speaker header with no content
            # from becoming a useless evidence segment.
            if not text:
                continue

            normalized_segments.append(
                TranscriptSegment(
                    segment_id=(
                        f"SEG-{segment_counter:04d}"
                    ),
                    speaker=self._clean_speaker(
                        segment["speaker"]
                    ),
                    timestamp_start=(
                        segment[
                            "timestamp_start"
                        ]
                    ),
                    timestamp_end=(
                        segment[
                            "timestamp_end"
                        ]
                    ),
                    text=text,
                    source_line_start=(
                        segment[
                            "source_line_start"
                        ]
                    ),
                    source_line_end=(
                        segment[
                            "source_line_end"
                        ]
                    ),
                )
            )

            segment_counter += 1

        # -----------------------------------------------------
        # Determine source format
        # -----------------------------------------------------

        source_format = self._get_source_format(
            detected_formats
        )

        # -----------------------------------------------------
        # Return normalized transcript
        # -----------------------------------------------------

        return NormalizedTranscript(
            segments=normalized_segments,
            original_text=original_text,
            source_format=source_format,
        )

    # =========================================================
    # LINE PARSING
    # =========================================================

    def _parse_line(
        self,
        line: str,
    ) -> dict | None:

        # -----------------------------------------------------
        # 1. Speaker + timestamp
        #
        # MUST be checked before speaker + timestamp + text.
        #
        # Examples:
        #
        # Sarah   00:10:15
        # Ravi Kumar(SS)   11:49
        # -----------------------------------------------------

        match = self.SPEAKER_TIMESTAMP_PATTERN.match(
            line
        )

        if match:

            speaker = match.group(
                "speaker"
            ).strip()

            timestamp = match.group(
                "timestamp"
            ).strip()

            if self._looks_like_speaker(
                speaker
            ):

                return {
                    "format": "speaker_timestamp",
                    "timestamp": timestamp,
                    "speaker": speaker,
                    "text": "",
                }

        # -----------------------------------------------------
        # 2. Timestamp + dash + speaker + text
        #
        # Example:
        #
        # 00:10:15 - Sarah: Hello everyone.
        # -----------------------------------------------------

        match = (
            self.TIMESTAMP_DASH_SPEAKER_PATTERN.match(
                line
            )
        )

        if match:

            return {
                "format": "timestamp_dash_speaker",
                "timestamp": match.group(
                    "timestamp"
                ).strip(),
                "speaker": match.group(
                    "speaker"
                ).strip(),
                "text": match.group(
                    "text"
                ).strip(),
            }

        # -----------------------------------------------------
        # 3. Timestamp + speaker + text
        #
        # Examples:
        #
        # [00:10:15] Sarah: Hello everyone.
        # 00:10:15 Sarah: Hello everyone.
        # -----------------------------------------------------

        match = self.TIMESTAMP_SPEAKER_PATTERN.match(
            line
        )

        if match:

            speaker = match.group(
                "speaker"
            ).strip()

            if self._looks_like_speaker(
                speaker
            ):

                return {
                    "format": "timestamp_speaker",
                    "timestamp": match.group(
                        "timestamp"
                    ).strip(),
                    "speaker": speaker,
                    "text": match.group(
                        "text"
                    ).strip(),
                }

        # -----------------------------------------------------
        # 4. Speaker + timestamp + text
        #
        # Examples:
        #
        # Sarah (00:10:15): Hello everyone.
        # Sarah(00:10:15): Hello everyone.
        # Sarah 00:10:15: Hello everyone.
        # -----------------------------------------------------

        match = (
            self.SPEAKER_TIMESTAMP_TEXT_PATTERN.match(
                line
            )
        )

        if match:

            speaker = match.group(
                "speaker"
            ).strip()

            if self._looks_like_speaker(
                speaker
            ):

                return {
                    "format": "speaker_timestamp_text",
                    "timestamp": match.group(
                        "timestamp"
                    ).strip(),
                    "speaker": speaker,
                    "text": match.group(
                        "text"
                    ).strip(),
                }

        # -----------------------------------------------------
        # 5. Speaker + colon + text
        #
        # Example:
        #
        # Sarah: Hello everyone.
        # -----------------------------------------------------

        match = self.SPEAKER_COLON_PATTERN.match(
            line
        )

        if match:

            speaker = match.group(
                "speaker"
            ).strip()

            if self._looks_like_speaker(
                speaker
            ):

                return {
                    "format": "speaker_colon",
                    "timestamp": None,
                    "speaker": speaker,
                    "text": match.group(
                        "text"
                    ).strip(),
                }

        # -----------------------------------------------------
        # Nothing recognized
        # -----------------------------------------------------

        return None

    # =========================================================
    # SPEAKER VALIDATION
    # =========================================================

    @staticmethod
    def _looks_like_speaker(
        value: str,
    ) -> bool:
        """
        Perform basic validation to avoid interpreting normal
        sentences as speaker names.
        """

        if not value:
            return False

        value = value.strip()

        # Speaker names normally aren't extremely long.
        if len(value) > 100:
            return False

        words = value.split()

        # Avoid treating long sentence fragments as speakers.
        if len(words) > 12:
            return False

        # Avoid treating obvious empty punctuation as a speaker.
        if not re.search(
            r"[A-Za-z0-9]",
            value,
        ):
            return False

        return True

    # =========================================================
    # TEXT CLEANING
    # =========================================================

    @staticmethod
    def _clean_text(
        text: str,
    ) -> str:
        """
        Normalize whitespace inside transcript text while
        preserving the actual words.
        """

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # =========================================================
    # SPEAKER CLEANING
    # =========================================================

    @staticmethod
    def _clean_speaker(
        speaker: str | None,
    ) -> str | None:
        """
        Normalize speaker whitespace.
        """

        if not speaker:
            return None

        speaker = re.sub(
            r"\s+",
            " ",
            speaker,
        )

        return speaker.strip()

    # =========================================================
    # SOURCE FORMAT DETECTION
    # =========================================================

    @staticmethod
    def _get_source_format(
        formats: set,
    ) -> str:
        """
        Return the detected transcript format.

        If multiple formats occur in the same transcript,
        return 'mixed'.
        """

        if not formats:
            return "unknown"

        if len(formats) == 1:
            return next(iter(formats))

        return "mixed"