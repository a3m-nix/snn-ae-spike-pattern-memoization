#!/bin/bash
# run_s7x_ij.sh — S7x-ij server: jalankan satu fase untuk kedua dataset berurutan (nice 10, core 9, satu thread).
# Pakai: nohup sudo -u jupyteruser -H bash run_s7x_ij.sh <check|accuracy|timing> &
set -u
cd "$(dirname "$0")"
PH=$1
PY=/home/jupyteruser/jupyter_env/bin/python
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TF_NUM_INTRAOP_THREADS=1 TF_NUM_INTEROP_THREADS=1
export TF_CPP_MIN_LOG_LEVEL=3
for ds in edge_iiotset ciciot2023; do
    echo "[$(date '+%F %T')] mulai $PH $ds | loadavg $(cat /proc/loadavg)"
    if ! nice -n 10 "$PY" -u s7x_ij.py --dataset "$ds" --phase "$PH" --core 9; then
        echo "[$(date '+%F %T')] $PH $ds GAGAL"; echo "failed:$PH:$ds" > logs/STATUS_$PH; exit 3
    fi
done
echo "done" > logs/STATUS_$PH
echo "[$(date '+%F %T')] $PH selesai"
