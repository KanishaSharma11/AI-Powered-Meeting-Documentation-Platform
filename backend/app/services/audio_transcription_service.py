"""
Audio-to-transcript pipeline (Stage 5). No speaker diarization —
every segment gets speaker=None ("Unknown" downstream) until that's
added (a documented extension point, not a bug).
"""
import os
import tempfile
from faster_whisper import WhisperModel
from app.core.config import settings
from app.schemas.transcript import NormalizedTranscript, TranscriptSegment


def _format_timestamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def transcribe_audio(audio_bytes: bytes, filename: str) -> NormalizedTranscript:
    suffix = os.path.splitext(filename)[1] or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        model = WhisperModel(settings.WHISPER_MODEL_SIZE, device=settings.WHISPER_DEVICE, compute_type=settings.WHISPER_COMPUTE_TYPE)
        segments_iter, _info = model.transcribe(tmp_path, vad_filter=True)
        segments: list[TranscriptSegment] = []
        counter = 0
        for seg in segments_iter:
            text = seg.text.strip()
            if not text:
                continue
            counter += 1
            segments.append(TranscriptSegment(
                segment_id=f"SEG-{counter:04d}", speaker=None,
                timestamp_start=_format_timestamp(seg.start), timestamp_end=_format_timestamp(seg.end),
                text=text, source_line_start=counter, source_line_end=counter,
            ))
        if not segments:
            raise ValueError("No speech detected in this audio file. If it contains speech, check the file isn't silent/corrupted.")
        return NormalizedTranscript(segments=segments, original_text=f"[audio file: {filename}, transcribed via Whisper]", source_format="whisper_audio")
    finally:
        os.remove(tmp_path)