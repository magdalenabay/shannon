from __future__ import annotations

from pathlib import Path

from ..registry import register
from ..runner import run
from ..types import Opts


IMAGE_FORMATS = ("png", "jpg", "gif", "bmp", "tiff", "ico", "webp")


def _magick_extras(out_fmt: str, opts: Opts) -> list[str]:
    args: list[str] = []
    if opts.scale:
        args += ["-resize", opts.scale]
    if out_fmt in ("jpg", "webp"):
        q = {"low": "60", "medium": "85", "high": "95"}[opts.quality]
        args += ["-quality", q]
    return args


@register(
    inputs=IMAGE_FORMATS,
    outputs=IMAGE_FORMATS,
    requires=("magick",),
    category="image",
    priority=10,
)
def image_to_image(src: Path, dst: Path, opts: Opts) -> None:
    out_fmt = dst.suffix.lstrip(".").lower()
    cmd = ["magick", str(src), *_magick_extras(out_fmt, opts), str(dst)]
    run(cmd, verbose=opts.verbose)


@register(
    inputs=("png", "jpg", "tiff", "bmp"),
    outputs=("webp",),
    requires=("cwebp",),
    category="image",
    priority=20,
)
def image_to_webp(src: Path, dst: Path, opts: Opts) -> None:
    q = {"low": "60", "medium": "80", "high": "95"}[opts.quality]
    cmd = ["cwebp", "-q", q, str(src), "-o", str(dst)]
    run(cmd, verbose=opts.verbose)


@register(
    inputs=("webp",),
    outputs=("png",),
    requires=("dwebp",),
    category="image",
    priority=20,
)
def webp_to_png(src: Path, dst: Path, opts: Opts) -> None:
    cmd = ["dwebp", str(src), "-o", str(dst)]
    run(cmd, verbose=opts.verbose)


@register(
    inputs=("heic",),
    outputs=("jpg", "png"),
    requires=("heif-convert",),
    category="image",
    priority=10,
)
def heic_to_image(src: Path, dst: Path, opts: Opts) -> None:
    out_fmt = dst.suffix.lstrip(".").lower()
    quality = {"low": "60", "medium": "85", "high": "95"}[opts.quality]
    if out_fmt == "jpg":
        cmd = ["heif-convert", "-q", quality, str(src), str(dst)]
    else:
        cmd = ["heif-convert", str(src), str(dst)]
    run(cmd, verbose=opts.verbose)


@register(
    inputs=IMAGE_FORMATS,
    outputs=("avif",),
    requires=("avifenc",),
    category="image",
    priority=20,
)
def image_to_avif(src: Path, dst: Path, opts: Opts) -> None:
    q = {"low": "30", "medium": "50", "high": "75"}[opts.quality]
    cmd = ["avifenc", "-q", q, str(src), str(dst)]
    run(cmd, verbose=opts.verbose)


@register(
    inputs=("avif",),
    outputs=("png", "jpg"),
    requires=("magick",),
    category="image",
    priority=10,
)
def avif_to_image(src: Path, dst: Path, opts: Opts) -> None:
    image_to_image(src, dst, opts)


@register(
    inputs=("svg",),
    outputs=("png", "jpg", "webp"),
    requires=("magick",),
    category="image",
    priority=10,
)
def svg_to_raster(src: Path, dst: Path, opts: Opts) -> None:
    out_fmt = dst.suffix.lstrip(".").lower()
    bg = ["-background", "none"] if out_fmt in ("png", "webp") else []
    cmd = ["magick", *bg, str(src), *_magick_extras(out_fmt, opts), str(dst)]
    run(cmd, verbose=opts.verbose)
