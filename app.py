import os
import logging
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from deep_translator import GoogleTranslator
except ImportError:  # pragma: no cover
    GoogleTranslator = None


def load_local_env():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_local_env()

logger = logging.getLogger("translation_service")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class ArticlePayload(BaseModel):
    title: str = ""
    description: str = ""
    category: str = ""
    subCategory: str = ""
    tags: list[str] = Field(default_factory=list)


class TranslationRequest(BaseModel):
    source_language: str = "en"
    target_language: str = "hi"
    items: list[ArticlePayload] = Field(default_factory=list)


class TextTranslationRequest(BaseModel):
    source_language: str = "en"
    target_language: str = "hi"
    texts: list[str] = Field(default_factory=list)


def validate_api_key(x_api_key: str | None) -> None:
    expected_api_key = os.getenv("TRANSLATION_SERVICE_API_KEY", "").strip()

    if expected_api_key and x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid translation service API key")


def get_translator(source_language: str, target_language: str):
    if GoogleTranslator is None:
        raise RuntimeError(
            "deep-translator is not installed. Run `pip install -r requirements.txt` first."
        )

    # GoogleTranslator mutates its internal URL params during translate().
    # Reusing one cached instance across concurrent requests can leak text
    # between requests and produce duplicated or wrong article content.
    return GoogleTranslator(source=source_language, target=target_language)


def translate_text(translator, value: str) -> str:
    if not value.strip():
        return value

    return translator.translate(value)


def translate_article_payload(translator, item: ArticlePayload) -> dict:
    return {
        "title": translate_text(translator, item.title),
        "description": translate_text(translator, item.description),
        "category": translate_text(translator, item.category),
        "subCategory": translate_text(translator, item.subCategory),
        "tags": [translate_text(translator, tag) for tag in item.tags if tag.strip()],
    }


def build_translation_response(source_language: str, target_language: str, payload_key: str, payload_value):
    return {
        "source_language": source_language,
        "target_language": target_language,
        "count": len(payload_value),
        payload_key: payload_value,
    }


app = FastAPI(title="News Translation Service", version="1.0.0")

allowed_origins = [
    origin.strip()
    for origin in (
        os.getenv("TRANSLATION_ALLOWED_ORIGINS")
        or ",".join(
            filter(
                None,
                [
                    os.getenv("CLIENT_APP_URL", "").strip(),
                    os.getenv("SERVER_API_URL", "").strip(),
                ],
            )
        )
    ).split(",")
    if origin.strip()
]

if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health")
def healthcheck():
    return {"ok": True, "service": "translation"}


@app.post("/translate/articles")
def translate_articles(
    payload: TranslationRequest,
    x_api_key: str | None = Header(default=None),
):
    validate_api_key(x_api_key)

    try:
        translator = get_translator(payload.source_language, payload.target_language)
        translated_items = [
            translate_article_payload(translator, item) for item in payload.items
        ]
    except Exception as exc:
        logger.exception(
            "Article translation failed: source=%s target=%s count=%s",
            payload.source_language,
            payload.target_language,
            len(payload.items),
        )
        raise HTTPException(
            status_code=502,
            detail=f"Translation provider request failed: {exc}",
        ) from exc

    return build_translation_response(
        payload.source_language,
        payload.target_language,
        "items",
        translated_items,
    )


@app.post("/translate/texts")
def translate_texts(
    payload: TextTranslationRequest,
    x_api_key: str | None = Header(default=None),
):
    validate_api_key(x_api_key)

    try:
        translator = get_translator(payload.source_language, payload.target_language)
        translated_texts = [translate_text(translator, text) for text in payload.texts]
    except Exception as exc:
        logger.exception(
            "Text translation failed: source=%s target=%s count=%s",
            payload.source_language,
            payload.target_language,
            len(payload.texts),
        )
        raise HTTPException(
            status_code=502,
            detail=f"Translation provider request failed: {exc}",
        ) from exc

    return build_translation_response(
        payload.source_language,
        payload.target_language,
        "texts",
        translated_texts,
    )
