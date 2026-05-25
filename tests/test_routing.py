from shannon import converters  # noqa: F401 — register everything
from shannon.routing import find_chain


def test_audio_to_audio_direct():
    chain = find_chain("mp3", "wav")
    assert chain is not None
    fmt_path, specs = chain
    assert fmt_path == ["mp3", "wav"]
    assert len(specs) == 1
    assert "ffmpeg" in specs[0].requires


def test_video_to_audio_direct():
    chain = find_chain("mp4", "mp3")
    assert chain is not None
    fmt_path, specs = chain
    assert fmt_path == ["mp4", "mp3"]
    assert len(specs) == 1


def test_video_to_gif_direct():
    chain = find_chain("webm", "gif")
    assert chain is not None
    _, specs = chain
    assert len(specs) == 1


def test_image_to_jpg_direct():
    chain = find_chain("png", "jpg")
    assert chain is not None


def test_structured_direct():
    chain = find_chain("json", "yaml")
    assert chain is not None
    _, specs = chain
    assert specs[0].category == "native"
    assert specs[0].requires == ()


def test_no_route():
    chain = find_chain("xyznotaformat", "alsonotaformat")
    assert chain is None


def test_same_format_noop():
    chain = find_chain("mp3", "mp3")
    assert chain is not None
    fmt_path, specs = chain
    assert specs == []


def test_pdf_to_txt_prefers_pdftotext_by_default():
    chain = find_chain("pdf", "txt")
    assert chain is not None
    _, specs = chain
    assert "pdftotext" in specs[0].requires


def test_pdf_to_txt_with_ocr_preference():
    chain = find_chain("pdf", "txt", prefer_category="ocr")
    assert chain is not None
    _, specs = chain
    assert specs[0].category == "ocr"
    assert "tesseract" in specs[0].requires


def test_image_to_txt_uses_ocr():
    chain = find_chain("png", "txt")
    assert chain is not None
    _, specs = chain
    # PNG -> TXT route is only via OCR.
    assert "tesseract" in specs[0].requires


def test_archive_native_repack_no_requires():
    chain = find_chain("zip", "tar.gz")
    assert chain is not None
    _, specs = chain
    assert specs[0].requires == ()


def test_subtitle_direct():
    chain = find_chain("srt", "vtt")
    assert chain is not None
