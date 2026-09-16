from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "AI-Powered Meeting Documentation Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # NOTE: no real credentials belong here — this is a generic placeholder.
    # Actual connection info must come from backend/.env (which is gitignored).
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/meeting_docs"
    )

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    # Stage 5: audio transcription (faster-whisper). "base" is a
    # reasonable default speed/accuracy tradeoff on CPU; bump to
    # "small"/"medium" for better accuracy if you have the CPU/GPU
    # headroom. compute_type "int8" runs on CPU without a GPU.
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    UPLOAD_DIR: str = "data/transcripts/uploads"
    NORMALIZED_DIR: str = "data/transcripts/normalized"
    GENERATED_DIR: str = "data/generated/mom"

    # Stage 6: JWT auth. JWT_SECRET_KEY MUST be overridden via a real
    # secret in production .env — this default is only safe for local
    # dev.
    JWT_SECRET_KEY: str = "change-me-in-production-this-is-not-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hour workday session

    # NOTE: no separate object store (e.g. MinIO) is used. Raw
    # transcript text lives in Postgres (transcript_segments), and
    # the MOM .docx is generated on-demand from DB state and streamed
    # straight to the client rather than persisted to disk/object
    # storage. Revisit if/when Stage 5 (audio files) needs real
    # binary storage — text alone doesn't need it.

    
    # --- Section 2.3: baseline confidence per capture source ---
    # Stage 1/2 only support "official_transcript" as an input source.
    # Bot audio / screen-share baselines are wired in now so Stage 5
    # (live audio capture) can plug in without touching this schema.
    SOURCE_BASELINE_CONFIDENCE: dict[str, float] = {
        "official_transcript": 0.99,
        "meeting_bot_audio": 0.92,
        "screen_share_audio": 0.88,
        "manual_notes": 0.80,
    }

    # Below this combined confidence, items are still shown in the
    # review UI but flagged for extra reviewer attention.
    LOW_CONFIDENCE_THRESHOLD: float = 0.75

    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()