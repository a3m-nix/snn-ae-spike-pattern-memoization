#!/usr/bin/env python3
"""S7p shim (ADDENDUM_S7P_03.md): pengganti fnirsi_logger.py untuk --fnirsi_path. Tidak membuka USB.
Membaca stream dari SATU logger yang tetap menyala ($FNIRSI_STREAM), mulai dari ujung berkas saat shim dibuka, dan
meneruskan setiap baris utuh ke stdout (flush per baris, polling 5 ms). Format baris = keluaran fnirsi_logger.py."""
import os, sys, time
path = os.environ["FNIRSI_STREAM"]
with open(path, "r", errors="replace") as f:
    f.seek(0, os.SEEK_END)
    buf = ""
    while True:
        chunk = f.readline()
        if not chunk:
            time.sleep(0.005)
            continue
        buf += chunk
        if buf.endswith("\n"):
            sys.stdout.write(buf); sys.stdout.flush(); buf = ""
