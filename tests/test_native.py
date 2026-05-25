import json

from shannon import converters  # noqa: F401
from shannon.converters.native import (
    csv_to_json,
    csv_to_yaml,
    json_to_csv,
    structured_convert,
)
from shannon.types import Opts


def test_json_to_yaml_roundtrip(tmp_path):
    src = tmp_path / "a.json"
    mid = tmp_path / "a.yaml"
    dst = tmp_path / "b.json"
    src.write_text(json.dumps({"a": 1, "b": [1, 2, 3], "c": "hello"}))
    structured_convert(src, mid, Opts())
    assert "a: 1" in mid.read_text()
    structured_convert(mid, dst, Opts())
    assert json.loads(dst.read_text()) == {"a": 1, "b": [1, 2, 3], "c": "hello"}


def test_json_to_toml(tmp_path):
    src = tmp_path / "a.json"
    dst = tmp_path / "a.toml"
    src.write_text(json.dumps({"server": {"host": "localhost", "port": 8080}}))
    structured_convert(src, dst, Opts())
    text = dst.read_text()
    assert "[server]" in text
    assert 'host = "localhost"' in text


def test_toml_to_yaml(tmp_path):
    src = tmp_path / "a.toml"
    dst = tmp_path / "a.yaml"
    src.write_text('[db]\nhost = "x"\nport = 5432\n')
    structured_convert(src, dst, Opts())
    out = dst.read_text()
    assert "db:" in out


def test_csv_to_json(tmp_path):
    src = tmp_path / "a.csv"
    dst = tmp_path / "a.json"
    src.write_text("name,age\nalice,30\nbob,25\n")
    csv_to_json(src, dst, Opts())
    assert json.loads(dst.read_text()) == [
        {"name": "alice", "age": "30"},
        {"name": "bob", "age": "25"},
    ]


def test_json_to_csv(tmp_path):
    src = tmp_path / "a.json"
    dst = tmp_path / "a.csv"
    src.write_text(json.dumps([{"x": 1, "y": 2}, {"x": 3, "y": 4}]))
    json_to_csv(src, dst, Opts())
    lines = dst.read_text().strip().splitlines()
    assert lines[0] == "x,y"
    assert lines[1] == "1,2"


def test_csv_to_yaml(tmp_path):
    src = tmp_path / "a.csv"
    dst = tmp_path / "a.yaml"
    src.write_text("k,v\nfoo,1\nbar,2\n")
    csv_to_yaml(src, dst, Opts())
    out = dst.read_text()
    assert "foo" in out and "bar" in out
