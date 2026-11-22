"""Tests unitaires pour commande_ai.py (sans besoin de token Discord ni d'OCR)."""
import io
from PIL import Image
import pytest

import commande_ai as mod


def test_split_into_chunks_empty():
    assert mod.split_into_chunks("") == []


def test_split_into_chunks_short():
    assert mod.split_into_chunks("bonjour") == ["bonjour"]


def test_split_into_chunks_respects_limit():
    text = "a" * 4000
    chunks = mod.split_into_chunks(text, limit=1900)
    assert len(chunks) == 3
    assert sum(len(c) for c in chunks) == 4000
    assert all(len(c) <= 1900 for c in chunks)


def test_split_into_chunks_respects_newlines():
    text = "ligne1\nligne2\n" + "x" * 3000
    chunks = mod.split_into_chunks(text, limit=100)
    joined = "".join(chunks)
    assert joined == text


def test_extract_text_from_image_returns_text():
    img = Image.new("RGB", (10, 10), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    text = mod.extract_text_from_image(buf.getvalue())
    assert isinstance(text, str)


def test_image_extensions_contains_common():
    assert ".png" in mod.IMAGE_EXTENSIONS
    assert ".jpg" in mod.IMAGE_EXTENSIONS
    assert ".jpeg" in mod.IMAGE_EXTENSIONS
