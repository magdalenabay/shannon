from __future__ import annotations

import platform as _platform
import shutil
from dataclasses import dataclass
from enum import Enum


class PkgMgr(Enum):
    BREW = "brew"
    APT = "apt-get"
    DNF = "dnf"
    PACMAN = "pacman"
    WINGET = "winget"
    SCOOP = "scoop"
    NONE = "none"


@dataclass
class PlatformInfo:
    os: str
    arch: str
    pkg_mgr: PkgMgr
    pkg_mgr_path: str | None


_CANDIDATES = {
    "macos": [PkgMgr.BREW],
    "linux": [PkgMgr.APT, PkgMgr.DNF, PkgMgr.PACMAN],
    "windows": [PkgMgr.SCOOP, PkgMgr.WINGET],
}


def detect() -> PlatformInfo:
    system = _platform.system().lower()
    if system == "darwin":
        os_name = "macos"
    elif system == "linux":
        os_name = "linux"
    elif system == "windows":
        os_name = "windows"
    else:
        os_name = system

    arch = _platform.machine().lower()

    pkg_mgr = PkgMgr.NONE
    pkg_path: str | None = None
    for cand in _CANDIDATES.get(os_name, []):
        path = shutil.which(cand.value)
        if path:
            pkg_mgr = cand
            pkg_path = path
            break

    return PlatformInfo(os=os_name, arch=arch, pkg_mgr=pkg_mgr, pkg_mgr_path=pkg_path)
