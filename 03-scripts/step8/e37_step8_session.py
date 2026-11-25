#!/usr/bin/env python3
"""
E3-7 native — langkah 8 (prereg/PREREG_STEP8_v1.md): orkestrator sesi live L8 pada layanan rev8.
Diturunkan dari e37_step7_session.py (helper diimpor dari modul itu dan dari e37v21_inject_A3, tidak disalin).
Perbedaan terhadap A7:
  - layanan rev8 (runner rev8 + filter F2), kunci prereg/LOCK_STEP8.sha256;
  - shadow 8 model (SNN_AE, Dense_AE runtime + 6 varian build benchmark); injeksi berikutnya menunggu insiden
    produksi DAN kedelapan shadow tertutup;
  - fase B: 60 menit benign (generator RPi + Kali) tanpa injeksi; fase M: 15 injeksi (ICMP/UDP/SYN × 5,
    1000 paket/s × 5 s), jeda tenang >= 60 s; tidak ada blok L/H.
Jalankan sebagai root di dalam e37-lock:  python3 -u e37_step8_session.py L8 | PF
  python3 e37_step8_session.py SCHEDULE   (sekali, sebelum kunci: tulis prereg/injection_schedule_step8.csv)
"""
import csv
import os
import random
import re
import sys
import time
from pathlib import Path

N7 = Path("/home/a3m-nix/disertasi-snn/23-e37-native")
sys.path.insert(0, str(N7 / "scripts"))
import e37_step7_session as S7  # noqa: E402

O = S7.O
STEP8 = N7 / "step8"
PREREG = N7 / "prereg"
SCHEDULE = PREREG / "injection_schedule_step8.csv"
LOCKF = PREREG / "LOCK_STEP8.sha256"
RUNNER = Path("/usr/local/sbin/snn-edge-live-run-rev8")
DROPIN = Path("/etc/systemd/system/snn-edge-live.service.d/rev8.conf")
MODELS = ("SNN_AE", "Dense_AE", "SNN_AE_B", "SNN_AE_REUSE", "SNN_AE_RQT", "Dense_AE_B", "Dense_AE_AQ3", "Dense_AE_AQ2")
PHASE_B_S = 3600
BG = ("1.75", "6300")                 # capture 1,75 jam, generator 6300 s (B 60 menit + M ±25 menit + cadangan)
O.BASE = STEP8
O.QUIET_S = 60
S7.MODELS = MODELS                    # states()/all_closed() membaca S7.MODELS


def write_schedule():
    if SCHEDULE.exists():
        sys.exit(f"{SCHEDULE} sudah ada (tidak ditimpa)")
    att = ["icmp", "udp", "syn"] * 5
    random.Random(8).shuffle(att)
    rep = {}
    with open(SCHEDULE, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["seq", "block", "attack", "pps", "rep", "interval_us", "duration_s"])
        for i, a in enumerate(att, 1):
            rep[a] = rep.get(a, 0) + 1
            w.writerow([i, "M", a, 1000, rep[a], 1000, 5])
    print("SCHEDULE", SCHEDULE, att)


def preflight(run):
    chk = {}
    chk["wlan0_conn"] = O.sh("/usr/bin/nmcli -g GENERAL.CONNECTION dev show wlan0")[1]
    rules = O.sh("/usr/sbin/ip rule show")[1]
    chk["rules"] = "1114:" in rules and "1063:" in rules
    chk["route_from_114"] = "dev wlan0" in O.sh(f"/usr/sbin/ip route get <REDACTED_INTERNAL_IP> from {O.TARGET}")[1]
    chk["arp_ignore"] = O.sh("/usr/sbin/sysctl -n net.ipv4.conf.all.arp_ignore")[1]
    rc, out, _ = O.kali(f"command -v hping3; ping -c1 -W1 {O.TARGET} >/dev/null; ip neigh show {O.TARGET}; "
                        f"timedatectl show -p NTPSynchronized --value")
    chk["kali"] = out.replace("\n", " | ")
    chk["kali_arp_wlan0_mac"] = "<REDACTED_MAC>" in out
    chk["rpi_ntp"] = O.sh("/usr/bin/timedatectl show -p NTPSynchronized --value")[1]
    chk["service"] = O.sh(f"/usr/bin/systemctl is-active {O.UNIT}")[1]
    chk["runner_rev8"] = "run-rev8" in O.sh(f"/usr/bin/systemctl show {O.UNIT} -p ExecStart --value")[1]
    chk["runner_has_f2"] = RUNNER.exists() and S7.F2 in RUNNER.read_text()
    chk["installed_eq_staged"] = bool(RUNNER.exists() and DROPIN.exists()
                                      and O.sha(RUNNER) == O.sha(STEP8 / "staging" / RUNNER.name)
                                      and O.sha(DROPIN) == O.sha(STEP8 / "staging" / DROPIN.name))
    bad = []
    for line in LOCKF.read_text().splitlines():
        p = line.split()
        if len(p) >= 2 and re.fullmatch(r"[0-9a-f]{64}", p[0]) and O.sha(p[-1]) != p[0]:
            bad.append(p[-1])
    chk["lock_mismatch"] = bad
    chk["free_gb"] = round(os.statvfs("/home").f_bavail * os.statvfs("/home").f_frsize / 1e9, 1)
    ok = (chk["wlan0_conn"] == "<REDACTED_SSID>" and chk["rules"] and chk["route_from_114"] and chk["arp_ignore"] == "1"
          and chk["kali_arp_wlan0_mac"] and "hping3" in chk["kali"] and chk["service"] == "active"
          and chk["runner_rev8"] and chk["runner_has_f2"] and chk["installed_eq_staged"] and not bad and chk["free_gb"] > 5)
    run.log("PREFLIGHT_OK" if ok else "PREFLIGHT_FAIL", **chk)
    return ok


def session_L8(run):
    O.restart_service(run, "session_start_clean_run")
    O.BG_CAPTURE_HOURS, O.BG_GEN_SECONDS = BG
    if not O.start_background(run):
        sys.exit("BACKGROUND_FAIL")
    S7.filter_check(run)
    t0 = time.time()
    run.log("PHASE_B_START", seconds=PHASE_B_S)
    while time.time() - t0 < PHASE_B_S:
        time.sleep(min(300, max(1, PHASE_B_S - (time.time() - t0))))
        run.log("TICK", elapsed_s=round(time.time() - t0), service=O.sh(f"/usr/bin/systemctl is-active {O.UNIT}")[1],
                restarts=sum("EDGE_LIVE_INTERFACE_RUNNING" in l for l in O.journal_since(t0)),
                shadow_errors=sum(("EDGE_SHADOW_ERROR" in l or "EDGE_SHADOW_DROP" in l) for l in O.journal_since(t0)))
    run.log("PHASE_B_END")
    run.log("PHASE_M_START")
    t0s = t0; last_end = time.time() - O.QUIET_S
    rows = list(csv.DictReader(open(SCHEDULE)))
    for row in rows:
        waited = 0
        while not S7.all_closed(t0s)[0] and waited < O.CLOSE_MAX_S:
            time.sleep(2); waited += 2
        closed, st = S7.all_closed(t0s)
        if not closed:
            run.log("NOT_CLOSED_BEFORE", seq=int(row["seq"]), state=st)    # tidak restart (output harus utuh)
        gap = O.QUIET_S - (time.time() - last_end)
        if gap > 0:
            time.sleep(gap)
        rpi_start = time.time()
        rc, out, _ = O.kali(f"date +%s.%N; timeout {O.ATTACK_S}s hping3 -q {O.HPING[row['attack']]} "
                            f"-i u{row['interval_us']} {O.TARGET} >/dev/null 2>&1; date +%s.%N", O.ATTACK_S + 30)
        rpi_end = time.time(); ks = out.split()
        run.log("INJECT", seq=int(row["seq"]), block=row["block"], attack=row["attack"], pps=int(row["pps"]),
                rep=int(row["rep"]), interval_us=int(row["interval_us"]), rc=rc,
                kali_start=float(ks[0]) if len(ks) >= 2 else None, kali_end=float(ks[-1]) if len(ks) >= 2 else None,
                rpi_ssh_start=rpi_start, rpi_ssh_end=rpi_end, waited_close_s=waited, state_before=st)
        last_end = rpi_end
    time.sleep(90)
    O.clock_offset(run, "end")
    O.restart_service(run, "session_end_write_outputs")
    run.log("SESSION_END", n=len(rows))


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else ""
    if tag == "SCHEDULE":
        return write_schedule()
    if os.geteuid() != 0 or tag not in ("L8", "PF"):
        sys.exit("usage (root): e37_step8_session.py L8|PF|SCHEDULE")
    os.environ["CAPTURE_FILTER"] = S7.F2
    run = O.Run(tag)
    run.log("SESSION_START", schedule_sha=O.sha(SCHEDULE), prereg_sha=O.sha(PREREG / "PREREG_STEP8_v1.md"))
    if not preflight(run):
        sys.exit("PREFLIGHT_FAIL")
    O.clock_offset(run, "start")
    if tag == "L8":
        session_L8(run)


if __name__ == "__main__":
    main()
