from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .types import Opts


ConverterFn = Callable[[Path, Path, Opts], None]


@dataclass(frozen=True)
class ConverterSpec:
    name: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    requires: tuple[str, ...]
    func: ConverterFn
    priority: int = 0
    heavy: bool = False
    category: str = "misc"


_REGISTRY: list[ConverterSpec] = []


def register(
    *,
    inputs,
    outputs,
    requires=(),
    priority: int = 0,
    heavy: bool = False,
    category: str = "misc",
):
    def deco(fn: ConverterFn) -> ConverterFn:
        spec = ConverterSpec(
            name=fn.__name__,
            inputs=tuple(s.lower() for s in inputs),
            outputs=tuple(s.lower() for s in outputs),
            requires=tuple(requires),
            func=fn,
            priority=priority,
            heavy=heavy,
            category=category,
        )
        _REGISTRY.append(spec)
        return fn

    return deco


def all_specs() -> list[ConverterSpec]:
    return list(_REGISTRY)


def find_direct(
    in_fmt: str,
    out_fmt: str,
    *,
    prefer_category: str | None = None,
) -> list[ConverterSpec]:
    matches = [s for s in _REGISTRY if in_fmt in s.inputs and out_fmt in s.outputs]
    if prefer_category:
        return sorted(
            matches,
            key=lambda s: (s.category != prefer_category, -s.priority, s.name),
        )
    return sorted(matches, key=lambda s: (-s.priority, s.name))


def all_backends() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for s in _REGISTRY:
        for r in s.requires:
            out.setdefault(r, set()).add(s.category)
    return out


def supported_inputs() -> set[str]:
    return {fmt for s in _REGISTRY for fmt in s.inputs}


def supported_outputs() -> set[str]:
    return {fmt for s in _REGISTRY for fmt in s.outputs}
