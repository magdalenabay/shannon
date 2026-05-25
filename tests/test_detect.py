from pathlib import Path

from shannon.detect import from_extension, parse_target


def test_simple_extension():
    assert from_extension(Path("foo.mp3")) == "mp3"


def test_uppercase():
    assert from_extension(Path("FOO.MP3")) == "mp3"


def test_alias_jpeg_to_jpg():
    assert from_extension(Path("foo.jpeg")) == "jpg"


def test_alias_yml_to_yaml():
    assert from_extension(Path("foo.yml")) == "yaml"


def test_compound_tar_gz():
    assert from_extension(Path("foo.tar.gz")) == "tar.gz"


def test_alias_tgz():
    assert from_extension(Path("foo.tgz")) == "tar.gz"


def test_no_extension():
    assert from_extension(Path("Makefile")) == ""


def test_parse_target_bare_extension(tmp_path):
    src = tmp_path / "foo.mp4"
    out, fmt = parse_target("mp3", src)
    assert out == tmp_path / "foo.mp3"
    assert fmt == "mp3"


def test_parse_target_path(tmp_path):
    src = tmp_path / "foo.mp4"
    target = tmp_path / "out" / "bar.mp3"
    out, fmt = parse_target(str(target), src)
    assert out == target
    assert fmt == "mp3"


def test_parse_target_compound(tmp_path):
    src = tmp_path / "foo.zip"
    out, fmt = parse_target("tar.gz", src)
    assert out == tmp_path / "foo.tar.gz"
    assert fmt == "tar.gz"


def test_parse_target_compound_source(tmp_path):
    """Source already has a compound extension; should strip then add new."""
    src = tmp_path / "foo.tar.gz"
    out, fmt = parse_target("zip", src)
    assert out == tmp_path / "foo.zip"
    assert fmt == "zip"


def test_parse_target_home_expansion(tmp_path, monkeypatch):
    src = tmp_path / "foo.mp4"
    monkeypatch.setenv("HOME", str(tmp_path))
    out, fmt = parse_target("~/out.mp3", src)
    assert str(out).startswith(str(tmp_path))
    assert fmt == "mp3"
