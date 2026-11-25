#!/usr/bin/env python3
"""Uji bit-identik pada kapasitas 2^12 dan 2^14 (DESIGN_CAPCHECK.md). Memakai s7i_rpi.phase_check tanpa perubahan."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "s7i"))
import s7i_rpi as I  # noqa: E402
I.CAPS3[:] = [12, 14]
if __name__ == "__main__":
    sys.argv += ["--phase", "check", "--result", str(HERE.parent / "0-revision-results-v2" / "s7k_capcheck")]
    I.G.main()
