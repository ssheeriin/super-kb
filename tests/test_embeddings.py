import io
from pathlib import Path

from skb import embeddings


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


def test_download_to_path_uses_cert_bundle(tmp_path: Path, monkeypatch) -> None:
    calls: dict[str, object] = {}
    destination = tmp_path / "model.bin"

    def fake_where() -> str:
        return "/tmp/fake-certifi.pem"

    def fake_context(*, cafile: str):
        calls["cafile"] = cafile
        return "ssl-context"

    def fake_urlopen(url: str, *, context):
        calls["url"] = url
        calls["context"] = context
        return _Response(b"payload")

    monkeypatch.setattr(embeddings.certifi, "where", fake_where)
    monkeypatch.setattr(embeddings.ssl, "create_default_context", fake_context)
    monkeypatch.setattr(embeddings.urllib.request, "urlopen", fake_urlopen)

    embeddings._download_to_path("https://example.invalid/model.bin", destination)

    assert destination.read_bytes() == b"payload"
    assert calls == {
        "cafile": "/tmp/fake-certifi.pem",
        "context": "ssl-context",
        "url": "https://example.invalid/model.bin",
    }
