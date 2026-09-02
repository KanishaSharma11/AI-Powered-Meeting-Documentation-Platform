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

    UPLOAD_DIR: str = "data/transcripts/uploads"
    NORMALIZED_DIR: str = "data/transcripts/normalized"
    GENERATED_DIR: str = "data/generated/mom"

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