from __future__ import annotations

import subprocess
from pathlib import Path


class ConvertError(RuntimeError):
    pass


def run(
    cmd: list[str],
    *,
    verbose: bool = False,
    cwd: Path | None = None,
    check: bool = True,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess:
    if verbose:
        print("$", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=not verbose,
            text=False if input_bytes is not None else True,
            input=input_bytes,
        )
    except FileNotFoundError as e:
        raise ConvertError(f"binary not found: {cmd[0]}") from e
    if check and result.returncode != 0:
        if not verbose:
            stderr = (
                result.stderr.decode(errors="replace")
                if isinstance(result.stderr, bytes)
                else (result.stderr or "")
            )
            tail = stderr.strip().splitlines()[-10:]
            msg = "\n  ".join(tail) if tail else "(no stderr)"
            raise ConvertError(f"{cmd[0]} failed (exit {result.returncode}):\n  {msg}")
        raise ConvertError(f"{cmd[0]} failed (exit {result.returncode})")
    return result
