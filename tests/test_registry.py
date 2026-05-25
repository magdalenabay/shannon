from shannon import converters  # noqa: F401
from shannon.registry import all_backends, all_specs, find_direct


def test_registry_populated():
    specs = all_specs()
    assert len(specs) > 10


def test_audio_converters_registered():
    matches = find_direct("mp3", "wav")
    assert matches, "expected at least one mp3 -> wav converter"


def test_backends_includes_ffmpeg():
    backends = all_backends()
    assert "ffmpeg" in backends
    assert "audio" in backends["ffmpeg"]


def test_priority_ordering():
    """When two converters serve png -> webp, the cwebp one (priority 20)
    should rank above the magick one (priority 10)."""
    matches = find_direct("png", "webp")
    if len(matches) >= 2:
        assert matches[0].priority >= matches[1].priority


def test_heavy_flag_on_office():
    matches = find_direct("docx", "pdf")
    if matches:
        assert any(m.heavy for m in matches)
