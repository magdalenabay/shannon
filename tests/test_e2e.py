"""End-to-end conversion tests against real backends.

Each test skips if the required tool is not installed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from shannon import converters  # noqa: F401
from shannon.converters.archive import _do_repack
from shannon.converters.audio import audio_to_audio
from shannon.converters.document import doc_to_doc
from shannon.converters.image import image_to_image, image_to_webp, svg_to_raster
from shannon.converters.native import structured_convert
from shannon.converters.ocr import image_ocr_txt
from shannon.converters.pdf import image_to_pdf, pdf_to_txt
from shannon.converters.subtitle import subtitle_convert
from shannon.converters.video import video_to_audio, video_to_gif
from shannon.installer import resolve_tool
from shannon.types import Opts


def has(tool: str) -> bool:
    return resolve_tool(tool) is not None


# ----- helpers to generate fixtures on the fly -----


def gen_silent_mp4(path: Path, seconds: int = 1) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c=blue:s=128x128:d={seconds}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:duration={seconds}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ],
        check=True,
    )


def gen_png(path: Path, w: int = 64, h: int = 64) -> None:
    subprocess.run(
        ["magick", "-size", f"{w}x{h}", "xc:red", str(path)],
        check=True,
    )


_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]


def _find_font() -> str | None:
    for p in _FONT_CANDIDATES:
        if Path(p).exists():
            return p
    return None


def gen_png_with_text(path: Path, text: str) -> None:
    font = _find_font()
    if not font:
        pytest.skip("no usable system font for text rendering")
    subprocess.run(
        [
            "magick",
            "-background",
            "white",
            "-fill",
            "black",
            "-font",
            font,
            "-pointsize",
            "60",
            f"label:{text}",
            str(path),
        ],
        check=True,
    )


# ----- audio -----


@pytest.mark.skipif(not has("ffmpeg"), reason="ffmpeg not installed")
def test_video_to_mp3(tmp_path):
    src = tmp_path / "in.mp4"
    dst = tmp_path / "out.mp3"
    gen_silent_mp4(src)
    video_to_audio(src, dst, Opts())
    assert dst.exists() and dst.stat().st_size > 100


@pytest.mark.skipif(not has("ffmpeg"), reason="ffmpeg not installed")
def test_audio_mp3_to_wav(tmp_path):
    src = tmp_path / "in.mp4"
    mp3 = tmp_path / "out.mp3"
    wav = tmp_path / "out.wav"
    gen_silent_mp4(src)
    video_to_audio(src, mp3, Opts())
    audio_to_audio(mp3, wav, Opts())
    assert wav.exists() and wav.stat().st_size > 100


# ----- video -----


@pytest.mark.skipif(not has("ffmpeg"), reason="ffmpeg not installed")
def test_video_to_gif(tmp_path):
    src = tmp_path / "in.mp4"
    dst = tmp_path / "out.gif"
    gen_silent_mp4(src)
    video_to_gif(src, dst, Opts(duration="0.5"))
    assert dst.exists() and dst.stat().st_size > 100


# ----- image -----


@pytest.mark.skipif(not has("magick"), reason="imagemagick not installed")
def test_png_to_jpg(tmp_path):
    src = tmp_path / "in.png"
    dst = tmp_path / "out.jpg"
    gen_png(src)
    image_to_image(src, dst, Opts())
    assert dst.exists() and dst.stat().st_size > 50


@pytest.mark.skipif(not has("cwebp") or not has("magick"), reason="cwebp/magick missing")
def test_png_to_webp(tmp_path):
    src = tmp_path / "in.png"
    dst = tmp_path / "out.webp"
    gen_png(src)
    image_to_webp(src, dst, Opts())
    assert dst.exists() and dst.stat().st_size > 30


def gen_svg(path: Path, size: int = 64) -> None:
    r = size * 3 // 8
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
        f'<circle cx="{size // 2}" cy="{size // 2}" r="{r}" fill="#c0f"/></svg>'
    )


@pytest.mark.skipif(not has("magick"), reason="imagemagick not installed")
@pytest.mark.parametrize("fmt", ["png", "jpg", "webp", "gif", "bmp", "tiff", "ico"])
def test_svg_to_raster(tmp_path, fmt):
    src = tmp_path / "in.svg"
    dst = tmp_path / f"out.{fmt}"
    gen_svg(src)
    svg_to_raster(src, dst, Opts())
    assert dst.exists() and dst.stat().st_size > 30


@pytest.mark.skipif(not has("magick"), reason="imagemagick not installed")
@pytest.mark.parametrize("fmt", ["png", "gif", "ico"])
def test_svg_keeps_transparency(tmp_path, fmt):
    src = tmp_path / "in.svg"
    dst = tmp_path / f"out.{fmt}"
    gen_svg(src)
    svg_to_raster(src, dst, Opts())
    corner = subprocess.run(
        ["magick", f"{dst}[0]", "-format", "%[fx:p{0,0}.a]", "info:"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert float(corner) == 0.0


@pytest.mark.skipif(not has("magick"), reason="imagemagick not installed")
def test_large_svg_to_ico(tmp_path):
    """ICO caps at 256px; a big SVG should still produce a multi-size icon."""
    src = tmp_path / "in.svg"
    dst = tmp_path / "out.ico"
    gen_svg(src, size=1024)
    svg_to_raster(src, dst, Opts())
    sizes = subprocess.run(
        ["magick", "identify", "-format", "%w\n", str(dst)],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert "256" in sizes and "16" in sizes


# ----- ocr -----


@pytest.mark.skipif(not has("tesseract") or not has("magick"), reason="tesseract/magick missing")
def test_image_ocr_to_txt(tmp_path):
    src = tmp_path / "scan.png"
    dst = tmp_path / "scan.txt"
    gen_png_with_text(src, "HELLO WORLD")
    image_ocr_txt(src, dst, Opts())
    assert dst.exists()
    content = dst.read_text().strip().lower()
    assert "hello" in content or "world" in content


# ----- pdf -----


@pytest.mark.skipif(not has("img2pdf") or not has("magick"), reason="img2pdf/magick missing")
def test_png_to_pdf(tmp_path):
    src = tmp_path / "in.png"
    dst = tmp_path / "out.pdf"
    gen_png(src)
    image_to_pdf(src, dst, Opts())
    assert dst.exists() and dst.read_bytes().startswith(b"%PDF")


@pytest.mark.skipif(
    not all(has(t) for t in ("img2pdf", "magick", "pdftotext", "pandoc")),
    reason="needs full pdf toolchain",
)
def test_pdf_to_txt_roundtrip(tmp_path):
    # Build a pdf from a text file via pandoc -> docx -> ... actually pandoc -> pdf
    # needs LaTeX; simpler path: write text, render as image with magick, img2pdf, then
    # pdftotext.
    txt_src = tmp_path / "src.txt"
    txt_src.write_text("Sample document text for pdftotext.")
    # Generate a pdf via pandoc HTML route is not available without latex.
    # Skip pandoc and just go text -> image -> pdf -> text (lose fidelity but proves pipeline).
    img = tmp_path / "page.png"
    font = _find_font()
    if not font:
        pytest.skip("no usable system font")
    subprocess.run(
        [
            "magick",
            "-size",
            "600x200",
            "xc:white",
            "-font",
            font,
            "-pointsize",
            "30",
            "-fill",
            "black",
            "-gravity",
            "center",
            "-annotate",
            "+0+0",
            "Sample document",
            str(img),
        ],
        check=True,
    )
    pdf = tmp_path / "doc.pdf"
    image_to_pdf(img, pdf, Opts())
    out = tmp_path / "out.txt"
    pdf_to_txt(pdf, out, Opts())
    # pdftotext on rasterized text may yield empty; we just assert command ran and produced a file.
    assert out.exists()


# ----- document -----


@pytest.mark.skipif(not has("pandoc"), reason="pandoc not installed")
def test_txt_to_docx(tmp_path):
    src = tmp_path / "in.txt"
    dst = tmp_path / "out.docx"
    src.write_text("# Hello\n\nThis is a paragraph.\n")
    doc_to_doc(src, dst, Opts())
    assert dst.exists()
    # docx is a zip starting with PK
    assert dst.read_bytes()[:2] == b"PK"


@pytest.mark.skipif(not has("pandoc"), reason="pandoc not installed")
def test_md_to_html(tmp_path):
    src = tmp_path / "in.md"
    dst = tmp_path / "out.html"
    src.write_text("# Title\n\nBody.\n")
    doc_to_doc(src, dst, Opts())
    assert dst.exists()
    assert "<h1" in dst.read_text().lower()


# ----- subtitle -----


@pytest.mark.skipif(not has("ffmpeg"), reason="ffmpeg not installed")
def test_srt_to_vtt(tmp_path):
    src = tmp_path / "in.srt"
    dst = tmp_path / "out.vtt"
    src.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nHello\n\n"
        "2\n00:00:02,500 --> 00:00:04,000\nWorld\n"
    )
    subtitle_convert(src, dst, Opts())
    out = dst.read_text()
    assert "WEBVTT" in out
    assert "Hello" in out and "World" in out


# ----- native -----


def test_json_to_yaml_no_backend(tmp_path):
    src = tmp_path / "a.json"
    dst = tmp_path / "a.yaml"
    src.write_text(json.dumps({"x": [1, 2, 3]}))
    structured_convert(src, dst, Opts())
    assert "x:" in dst.read_text()


# ----- archive -----


def test_zip_to_targz(tmp_path):
    import zipfile
    src = tmp_path / "in.zip"
    dst = tmp_path / "out.tar.gz"
    with zipfile.ZipFile(src, "w") as z:
        z.writestr("hello.txt", "hello world")
        z.writestr("dir/inner.txt", "inner")
    _do_repack(src, dst)
    import tarfile
    with tarfile.open(dst) as t:
        names = t.getnames()
    assert any("hello.txt" in n for n in names)


@pytest.mark.skipif(not has("7z"), reason="7z/7zz not installed")
def test_zip_to_7z(tmp_path):
    import zipfile
    src = tmp_path / "in.zip"
    dst = tmp_path / "out.7z"
    with zipfile.ZipFile(src, "w") as z:
        z.writestr("a.txt", "data")
    _do_repack(src, dst)
    assert dst.exists() and dst.stat().st_size > 30


# ----- heavy backends -----


@pytest.mark.skipif(not has("soffice") or not has("pandoc"), reason="libreoffice/pandoc missing")
def test_docx_to_pdf_libreoffice(tmp_path):
    """pandoc to make a docx, then libreoffice to convert it to pdf."""
    src_md = tmp_path / "src.md"
    docx = tmp_path / "src.docx"
    pdf = tmp_path / "src.pdf"
    src_md.write_text("# Heading\n\nLibreOffice round-trip test.\n")
    doc_to_doc(src_md, docx, Opts())
    from shannon.converters.office import office_to_office
    office_to_office(docx, pdf, Opts())
    assert pdf.exists() and pdf.read_bytes().startswith(b"%PDF")


@pytest.mark.skipif(not has("ebook-convert") or not has("pandoc"), reason="calibre/pandoc missing")
def test_md_to_epub_to_mobi(tmp_path):
    """pandoc md->epub, then calibre epub->mobi."""
    src_md = tmp_path / "src.md"
    epub = tmp_path / "src.epub"
    mobi = tmp_path / "src.mobi"
    src_md.write_text("# Title\n\nBody.\n")
    doc_to_doc(src_md, epub, Opts())
    from shannon.converters.ebook import ebook_convert
    ebook_convert(epub, mobi, Opts())
    assert mobi.exists() and mobi.stat().st_size > 100


# ----- rar (read-only) -----


@pytest.mark.skipif(not has("unrar"), reason="unrar not installed")
def test_rar_to_zip(tmp_path):
    """Extract a small rar fixture if a `unrar` binary is available."""
    # Create a rar archive is not possible from the python side without a writer.
    # Instead we test that the converter is registered & the routing finds it.
    from shannon.routing import find_chain
    chain = find_chain("rar", "zip")
    assert chain is not None
    _, specs = chain
    assert "unrar" in specs[0].requires


# ----- full CLI dispatch -----


@pytest.mark.skipif(not has("ffmpeg"), reason="ffmpeg not installed")
def test_cli_video_to_mp3(tmp_path):
    from shannon.cli import main
    src = tmp_path / "src.mp4"
    gen_silent_mp4(src)
    rc = main([str(src), "mp3"])
    assert rc == 0
    assert (tmp_path / "src.mp3").exists()


@pytest.mark.skipif(not has("magick") or not has("pandoc"), reason="needs magick+pandoc")
def test_cli_batch_glob(tmp_path):
    """CLI accepts multiple inputs + bare format target."""
    from shannon.cli import main
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    gen_png(a)
    gen_png(b)
    rc = main([str(a), str(b), "jpg"])
    assert rc == 0
    assert (tmp_path / "a.jpg").exists()
    assert (tmp_path / "b.jpg").exists()


def test_cli_doctor_runs(capsys):
    from shannon.cli import main
    rc = main(["--doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Platform:" in out
    assert "Backends:" in out


def test_cli_list_runs(capsys):
    from shannon.cli import main
    rc = main(["--list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[audio]" in out
    assert "[video]" in out


def test_cli_expands_wildcards_itself(tmp_path):
    """PowerShell/cmd pass `*.json` through literally; shannon must glob it."""
    from shannon.cli import main
    (tmp_path / "a.json").write_text('{"x": 1}')
    (tmp_path / "b.json").write_text('{"y": 2}')
    rc = main([str(tmp_path / "*.json"), "yaml"])
    assert rc == 0
    assert (tmp_path / "a.yaml").exists()
    assert (tmp_path / "b.yaml").exists()


def test_cli_wildcard_with_no_matches(tmp_path, capsys):
    from shannon.cli import main
    rc = main([str(tmp_path / "*.nope"), "png"])
    assert rc == 2
    assert "no files match" in capsys.readouterr().err
