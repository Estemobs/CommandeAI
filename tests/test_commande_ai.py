import asyncio
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import commande_ai  # noqa: E402


class FakeResponse:
    def __init__(self, content=b"", content_type="image/png", status=200):
        self.content = content
        self.headers = {"Content-Type": content_type}
        self.status_code = status
        self.closed = False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise commande_ai.requests.HTTPError(f"HTTP {self.status_code}")

    def iter_content(self, chunk_size=1):
        for start in range(0, len(self.content), chunk_size):
            yield self.content[start:start + chunk_size]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True


def _png_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_download_image_has_timeout(monkeypatch):
    seen = {}

    def fake_get(url, **kwargs):
        seen.update(kwargs)
        return FakeResponse(_png_bytes())

    monkeypatch.setattr(commande_ai.requests, "get", fake_get)

    assert commande_ai.download_image("https://example.test/image.png") == _png_bytes()
    assert seen["timeout"] == commande_ai.IMAGE_FETCH_TIMEOUT
    assert seen["stream"] is True


def test_download_image_rejects_non_image(monkeypatch):
    monkeypatch.setattr(
        commande_ai.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(b"<html>", "text/html"),
    )

    with pytest.raises(ValueError, match="image"):
        commande_ai.download_image("https://example.test/page")


def test_download_image_rejects_oversized_payload(monkeypatch):
    monkeypatch.setattr(
        commande_ai.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(b"x" * 64, "image/png"),
    )

    with pytest.raises(ValueError, match="volumineuse"):
        commande_ai.download_image("https://example.test/big.png", max_bytes=32)


def test_improve_image_quality_returns_jpeg(monkeypatch):
    monkeypatch.setattr(
        commande_ai.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(_png_bytes()),
    )

    result = commande_ai.improve_image_quality("https://example.test/image.png")

    assert result.startswith(b"\xff\xd8")


def test_is_expected_response_only_accepts_same_author_and_channel():
    author = SimpleNamespace(id=1)
    channel = SimpleNamespace(id=2)
    other = SimpleNamespace(id=3)

    assert commande_ai._is_expected_response(
        SimpleNamespace(author=author, channel=channel), author, channel
    )
    assert not commande_ai._is_expected_response(
        SimpleNamespace(author=other, channel=channel), author, channel
    )
    assert not commande_ai._is_expected_response(
        SimpleNamespace(author=author, channel=other), author, channel
    )


def test_display_text_sends_the_extracted_text():
    ctx = SimpleNamespace(send=AsyncMock())

    asyncio.run(commande_ai.display_text(ctx, "bonjour"))

    ctx.send.assert_awaited_once()
    embed = ctx.send.await_args.kwargs["embed"]
    assert embed.description == "bonjour"


def test_display_text_handles_empty_text():
    ctx = SimpleNamespace(send=AsyncMock())

    asyncio.run(commande_ai.display_text(ctx, "   "))

    ctx.send.assert_awaited_once_with("Aucun texte détecté dans l'image.")


def test_intents_are_minimal():
    assert commande_ai.intents.message_content is True
    assert commande_ai.intents.presences is False
    assert commande_ai.intents.members is False


def test_load_discord_token_from_explicit_path(tmp_path):
    secrets = tmp_path / "secrets.json"
    secrets.write_text(json.dumps({"discord_bot_token": "test-token"}))

    assert commande_ai._load_discord_token(secrets) == "test-token"


def test_load_discord_token_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        commande_ai._load_discord_token(tmp_path / "missing.json")
