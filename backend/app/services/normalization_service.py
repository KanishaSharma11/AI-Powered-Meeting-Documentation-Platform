import re
from app.schemas.transcript import NormalizedTranscript, TranscriptSegment

class TranscriptNormalizationService:
    """
    Normalizes different transcript formats into a common internal
    representation. Supports: "Speaker  timestamp" (two-line style),
    "[timestamp] Speaker: text", "Speaker (timestamp): text",
    "Speaker [timestamp]: text", "timestamp - Speaker: text",
    "Speaker: text". Continuation lines attach to the preceding
    speaker segment.
    """
    TIMESTAMP_PATTERN = r"\d{1,2}:\d{2}(?::\d{2})?"
    SPEAKER_TIMESTAMP_PATTERN = re.compile(r"^\s*(?P<speaker>.+?)\s+(?P<timestamp>" + TIMESTAMP_PATTERN + r")\s*$")
    TIMESTAMP_SPEAKER_PATTERN = re.compile(r"^\s*\[?(?P<timestamp>" + TIMESTAMP_PATTERN + r")\]?\s+(?P<speaker>.+?)\s*:\s*(?P<text>.*)$")
    # FIX: accepts either bracket style around the timestamp — originally
    # only matched parentheses, so "Sarah [00:10:15]: text" (square
    # brackets after speaker) was mis-parsed.
    SPEAKER_TIMESTAMP_TEXT_PATTERN = re.compile(r"^\s*(?P<speaker>.+?)\s+[\(\[]?(?P<timestamp>" + TIMESTAMP_PATTERN + r")[\)\]]?\s*:?\s*(?P<text>.+)$")
    SPEAKER_COLON_PATTERN = re.compile(r"^\s*(?P<speaker>[^:\n]{1,100})\s*:\s*(?P<text>.+)$")
    TIMESTAMP_DASH_SPEAKER_PATTERN = re.compile(r"^\s*\[?(?P<timestamp>" + TIMESTAMP_PATTERN + r")\]?\s*[-\u2013\u2014]\s*(?P<speaker>[^:\n]{1,100})\s*:?\s*(?P<text>.*)$")

    def normalize(self, transcript: str) -> NormalizedTranscript:
        if not transcript or not transcript.strip():
            raise ValueError("Transcript cannot be empty.")
        original_text = transcript
        lines = transcript.splitlines()
        segments = []
        current_segment = None
        detected_formats = set()
        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue
            parsed = self._parse_line(line)
            if parsed:
                if current_segment is not None:
                    segments.append(current_segment)
                current_segment = {"speaker": parsed.get("speaker"), "timestamp_start": parsed.get("timestamp"),
                    "timestamp_end": None, "text": parsed.get("text", ""), "source_line_start": line_number, "source_line_end": line_number}
                detected_formats.add(parsed.get("format", "unknown"))
            else:
                if current_segment is not None:
                    current_text = current_segment["text"]
                    current_segment["text"] = (current_text + " " + line) if current_text else line
                    current_segment["source_line_end"] = line_number
                else:
                    current_segment = {"speaker": None, "timestamp_start": None, "timestamp_end": None,
                        "text": line, "source_line_start": line_number, "source_line_end": line_number}
                    detected_formats.add("unidentified")
        if current_segment is not None:
            segments.append(current_segment)
        normalized_segments = []
        segment_counter = 1
        for segment in segments:
            text = self._clean_text(segment["text"])
            if not text:
                continue
            normalized_segments.append(TranscriptSegment(
                segment_id=f"SEG-{segment_counter:04d}", speaker=self._clean_speaker(segment["speaker"]),
                timestamp_start=segment["timestamp_start"], timestamp_end=segment["timestamp_end"], text=text,
                source_line_start=segment["source_line_start"], source_line_end=segment["source_line_end"]))
            segment_counter += 1
        return NormalizedTranscript(segments=normalized_segments, original_text=original_text,
            source_format=self._get_source_format(detected_formats))

    def _parse_line(self, line: str):
        match = self.SPEAKER_TIMESTAMP_PATTERN.match(line)
        if match:
            speaker = match.group("speaker").strip(); timestamp = match.group("timestamp").strip()
            if self._looks_like_speaker(speaker):
                return {"format": "speaker_timestamp", "timestamp": timestamp, "speaker": speaker, "text": ""}
        match = self.TIMESTAMP_DASH_SPEAKER_PATTERN.match(line)
        if match:
            return {"format": "timestamp_dash_speaker", "timestamp": match.group("timestamp").strip(),
                "speaker": match.group("speaker").strip(), "text": match.group("text").strip()}
        match = self.TIMESTAMP_SPEAKER_PATTERN.match(line)
        if match:
            speaker = match.group("speaker").strip()
            if self._looks_like_speaker(speaker):
                return {"format": "timestamp_speaker", "timestamp": match.group("timestamp").strip(),
                    "speaker": speaker, "text": match.group("text").strip()}
        match = self.SPEAKER_TIMESTAMP_TEXT_PATTERN.match(line)
        if match:
            speaker = match.group("speaker").strip()
            if self._looks_like_speaker(speaker):
                return {"format": "speaker_timestamp_text", "timestamp": match.group("timestamp").strip(),
                    "speaker": speaker, "text": match.group("text").strip()}
        match = self.SPEAKER_COLON_PATTERN.match(line)
        if match:
            speaker = match.group("speaker").strip()
            if self._looks_like_speaker(speaker):
                return {"format": "speaker_colon", "timestamp": None, "speaker": speaker, "text": match.group("text").strip()}
        return None

    @staticmethod
    def _looks_like_speaker(value: str) -> bool:
        if not value: return False
        value = value.strip()
        if len(value) > 100: return False
        if len(value.split()) > 12: return False
        if not re.search(r"[A-Za-z0-9]", value): return False
        return True

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _clean_speaker(speaker):
        if not speaker: return None
        return re.sub(r"\s+", " ", speaker).strip()

    @staticmethod
    def _get_source_format(formats: set) -> str:
        if not formats: return "unknown"
        if len(formats) == 1: return next(iter(formats))
        return "mixed"