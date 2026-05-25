from __future__ import annotations

import csv
import json
from pathlib import Path

from ..registry import register
from ..types import Opts

try:
    import tomllib
except ImportError:
    tomllib = None  # type: ignore[assignment]

try:
    import yaml as _yaml
except ImportError:
    _yaml = None  # type: ignore[assignment]

try:
    import tomli_w as _tomli_w
except ImportError:
    _tomli_w = None  # type: ignore[assignment]


STRUCTURED = ("json", "yaml", "toml")


def _load_structured(src: Path):
    ext = src.suffix.lstrip(".").lower()
    if ext == "yml":
        ext = "yaml"
    if ext == "json":
        return json.loads(src.read_text())
    if ext == "yaml":
        if _yaml is None:
            raise RuntimeError("pyyaml not installed")
        return _yaml.safe_load(src.read_text())
    if ext == "toml":
        if tomllib is None:
            raise RuntimeError("python 3.11+ required for toml read")
        return tomllib.loads(src.read_text())
    raise ValueError(f"not a structured format: {ext}")


def _dump_structured(data, dst: Path) -> None:
    ext = dst.suffix.lstrip(".").lower()
    if ext == "yml":
        ext = "yaml"
    if ext == "json":
        dst.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    elif ext == "yaml":
        if _yaml is None:
            raise RuntimeError("pyyaml not installed")
        dst.write_text(
            _yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        )
    elif ext == "toml":
        if _tomli_w is None:
            raise RuntimeError("tomli-w not installed")
        if not isinstance(data, dict):
            raise ValueError("toml output requires a dict at the top level")
        dst.write_text(_tomli_w.dumps(data))
    else:
        raise ValueError(f"not a structured format: {ext}")


@register(
    inputs=STRUCTURED,
    outputs=STRUCTURED,
    requires=(),
    category="native",
    priority=10,
)
def structured_convert(src: Path, dst: Path, opts: Opts) -> None:
    data = _load_structured(src)
    _dump_structured(data, dst)


@register(
    inputs=("csv",),
    outputs=("json",),
    requires=(),
    category="native",
    priority=10,
)
def csv_to_json(src: Path, dst: Path, opts: Opts) -> None:
    with src.open(newline="") as f:
        rows = list(csv.DictReader(f))
    dst.write_text(json.dumps(rows, indent=2, ensure_ascii=False))


@register(
    inputs=("json",),
    outputs=("csv",),
    requires=(),
    category="native",
    priority=10,
)
def json_to_csv(src: Path, dst: Path, opts: Opts) -> None:
    data = json.loads(src.read_text())
    if not isinstance(data, list) or not data:
        raise ValueError("json -> csv requires a non-empty list of objects")
    if not isinstance(data[0], dict):
        raise ValueError("json -> csv requires a list of objects")
    keys: list[str] = []
    for r in data:
        for k in r:
            if k not in keys:
                keys.append(k)
    with dst.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in data:
            w.writerow(r)


@register(
    inputs=("csv",),
    outputs=("yaml",),
    requires=(),
    category="native",
    priority=10,
)
def csv_to_yaml(src: Path, dst: Path, opts: Opts) -> None:
    if _yaml is None:
        raise RuntimeError("pyyaml not installed")
    with src.open(newline="") as f:
        rows = list(csv.DictReader(f))
    dst.write_text(_yaml.safe_dump(rows, sort_keys=False, allow_unicode=True))
